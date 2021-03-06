#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pylint: disable=E1103
import math
import numpy as np
from collections import Iterable
from ..util.misc import randn_c


# noinspection PyPep8
def generate_jakes_samples(Fd, Ts=1e-3, NSamples=100, L=8, shape=None,
                           current_time=0, phi_l=None, psi_l=None):
    """
    Generates channel samples according to the Jakes model.

    This functions generates channel samples for a single tap according to
    the Jakes model given by

    .. math::
       :label: jakes_model

       h(t) = \\frac{1}{\\sqrt{L}}\\sum_{l=0}^{L-1}\\exp\\{j[2\\pi f_D \\cos(\\phi_l)t+\\psi_l]\\}

    Parameters
    ----------
    Fd : float
        The Doppler frequency (in Hertz).
    Ts : float
        The sample interval (in seconds).
    NSamples : int
        The number of samples to generate.
    L : int
        The number of rays for the Jakes model.
    shape : tuple[int]
        The shape of the generated channel. This is used to generate MIMO
        channels. For instance, in order to generate channels samples for a
        MIMO scenario with 3 receive antennas and 2 transmit antennas use a
        shape of (3, 2).
    current_time : float
        The current start time
    phi_l : np.ndarray
        The "phi" part in Jakes model
    psi_l : np.ndarray
        The "psi" part in Jakes model

    Returns
    -------
    (float, np.ndarray)
        The **first element** in the returned tuple is the **new current
        time** (that should be used the next time this function is called to
        'continue' the fading).

        The **second** element in the returned tuple is the **generated
        channel**. If `shape` is None the the shape of the returned h is
        equal to ( NSamples,). That is, h is a 1-dimensional numpy array. If
        `shape` was provided then the shape of h is the provided shape with
        an additional dimension for the time (the last dimension). For
        instance, if a `shape` of (3, 2) was provided then the shape of the
        returned h will be (3, 2, NSamples).
    """
    # Generate time samples
    t = np.arange(
        current_time,  # Start time
        NSamples * Ts + current_time,
        Ts * 1.0000000001)

    if phi_l is None:
        if shape is None:
            phi_l = np.random.rand(L, 1)
        else:
            phi_l = np.random.rand(L, *shape, 1)

    if psi_l is None:
        if shape is None:
            psi_l = np.random.rand(L, 1)
        else:
            psi_l = np.random.rand(L, *shape, 1)

    # Update the self._current_time variable with the value of the next
    # time sample that should be generated when _generate_time_samples
    # is called again.
    new_current_time = t[-1] + Ts

    h = (math.sqrt(1.0 / L) *
         np.sum(np.exp(1j * (2 * np.pi * Fd
                             * np.cos(phi_l) * t + psi_l)),
                axis=0))

    return new_current_time, h


class FadingSampleGenerator(object):
    """
    Base class for fading generators.

    Parameters
    ----------
    shape : tuple[int] | int, optional
        The shape of the sample generator. Each time
        `generate_more_samples(num_samples)` method is called it will
        generate samples with this shape as the first dimensions.
    """
    def __init__(self, shape=None):
        self._shape = shape

        # Set this variable in a derived class with the next samples
        # everytime the generate_more_samples method is called. Note that
        # generate_more_samples should take the value of self._shape into
        # account.
        self._samples = None

    @property
    def shape(self):
        """
        Get the shape of the sampling generator

        This is the shape of the samples that will be generated (not
        including num_samples).

        Returns
        -------
        tuple[int] | None
        """
        if self._shape is not None and not isinstance(self._shape,
                                                      Iterable):
            shape = (self._shape, )
        else:
            shape = self._shape

        return shape

    @shape.setter
    def shape(self, new_shape):
        """
        Set the shape of the sampling generator.

        This is the shape of the samples that will be generated (not
        including num_samples).

        Parameters
        ----------
        new_shape : None | int | tuple[int]
            The shape of the generated channel.
        """
        self._shape = new_shape

    def get_samples(self):
        """
        Get the last generated sample.

        Returns
        -------
        np.ndarray
        """
        return self._samples

    def generate_more_samples(self, num_samples=None):  # pragma: nocover
        """
        Generate next samples.

        When implementing this method in a subclass you must take the value
        of the self._shape attribute into account.

        Parameters
        ----------
        num_samples : int, optional
            Number of samples (with the provided shape) to generate. If not
            provided it will be assumed to be 1.
        """
        raise NotImplementedError("Implement in a subclass")

    def skip_samples_for_next_generation(
            self, num_samples):  # pragma: no cover
        """
        Advance sample generation process by `num_samples` similarly to
        what would happen if you call `generate_more_samples(
        num_samples=num_samples)`, but without actually generating the
        samples.

        Parameters
        ----------
        num_samples : int
            How many samples to skip.
        """
        raise NotImplementedError("Implement in a subclass")

    def get_similar_fading_generator(self):  # pragma: no cover
        """
        Get a similar fading generator with the same configuration,
        but that generates independent samples.
        """
        # Note: Don't forget to copy self._shape in subclasses, besides any
        # member attribute in the subclass
        raise NotImplementedError("Implement in a subclass")


class RayleighSampleGenerator(FadingSampleGenerator):
    """
    Class that generates fading samples from a Raleigh distribution.

    Parameters
    ----------
    shape : int | tuple[int] | None
        The shape of the sample generator. Each time the
        `generate_jakes_samples` method is called it will generate samples
        with this shape. If not provided, then 1 will be assumed.
    """

    def __init__(self, shape=None):
        super(RayleighSampleGenerator, self).__init__(shape)

        # Generate first sample
        self.generate_more_samples()

    def generate_more_samples(self, num_samples=None):
        """
        Generate next samples.

        Parameters
        ----------
        num_samples : int, optional
            Number of samples (with the provided shape) to generate. If not
            provided it will be assumed to be 1.
        """
        shape = self.shape

        if num_samples is None:
            if shape is None:
                self._samples = randn_c()
            else:
                # noinspection PyArgumentList
                self._samples = randn_c(*shape)
        elif self.shape is None:
            self._samples = randn_c(num_samples)
        else:
            shape = list(shape)
            shape.append(num_samples)
            self._samples = randn_c(*shape)

    def skip_samples_for_next_generation(self,
                                         num_samples):  # pragma: no cover
        """
        Advance sample generation process by `num_samples` similarly to
        what would happen if you call `generate_more_samples(
        num_samples=num_samples)`, but without actually generating the
        samples.

        Since the samples generated by RayleighSampleGenerator are
        independent, calling this method has no effect.

        Parameters
        ----------
        num_samples : int
            How many samples to skip. This is ignored in the
            RayleighSampleGenerator. Since the different samples are
            uncorrelated then calling `skip_samples_for_next_generation`
            does not do anything.
        """
        pass

    def get_similar_fading_generator(self):
        """
        Get a similar fading generator with the same configuration,
        but that generates independent samples.

        Returns
        -------
        RayleighSampleGenerator
            Another RayleighSampleGenerator object with the same
            configuration of this object.
        """
        return RayleighSampleGenerator(self._shape)


# TODO: Remove the RS parameter or make it work with the
# get_similar_fading_generator method.  You could also move it to the base
# class and add it as an argument to RayleighSampleGenerator
# noinspection PyPep8
class JakesSampleGenerator(FadingSampleGenerator):
    """
    Class that generated fading samples according to the Jakes model given
    by

    .. math:: h(t) = \\frac{1}{\\sqrt{L}}\\sum_{l=0}^{L-1}\\exp\\{j[2\\pi f_D \\cos(\\phi_l)t+\\psi_l]\\}

    Parameters
    ----------
    Fd : float
        The Doppler frequency (in Hertz).
    Ts : float
        The sample interval (in seconds).
    L : int
        The number of rays for the Jakes model.
    shape : int | tuple[int], optional
        The shape of the sample generator. Each time the
        `generate_jakes_samples` method is called it will generate samples
        with this shape. If not provided, then 1 will be assumed. This
        could be used to generate MIMO channels. For instance, in order to
        generate channels samples for a MIMO scenario with 3 receive
        antennas and 2 transmit antennas use a shape of (3, 2).
    RS : np.random.RandomState
        The RandomState object used to generate the random values. If not
        provided, the global RandomState in numpy will be used.

    See also
    --------
    generate_jakes_samples
    """

    def __init__(self, Fd=100, Ts=1e-3, L=8, shape=None, RS=None):
        super(JakesSampleGenerator, self).__init__(shape)

        self._Fd = Fd
        self._Ts = Ts
        self._L = L

        self._phi_l = None  # This will be set in the set_shape method
        self._psi_l = None  # This will be set in the set_shape method

        if RS is None:
            # If RS was not provided, we set it to the numpy.random
            # module. That way, when the rand "method" in RS is called it
            # will actually call the global rand function in numpy.random.
            # RandomState object in numpy.
            RS = np.random
        self.RS = RS

        # self._current_time will be update after each call to the
        # `generate_more_samples` method.
        self._current_time = 0.0

        # Update self._phi_l and self._psi_l according to self._shape
        self._set_phi_and_psi_according_to_shape()

        # Generate first sample
        self.generate_more_samples()

    @property
    def shape(self):
        """
        Get the shape of the sampling generator

        This is the shape of the samples that will be generated (not
        including num_samples).

        Returns
        -------
        tuple[int] | None
        """
        return super(JakesSampleGenerator, self).shape

    @shape.setter
    def shape(self, new_shape):
        """
        Set the shape of the sampling generator.

        This is the shape of the samples that will be generated (not
        including num_samples).

        Parameters
        ----------
        new_shape : None | int | tuple[int]
            The shape of the generated channel.
        """
        self._shape = new_shape
        # Since phi and psi depend on the shape we need to update
        # them. Note that `_set_phi_and_psi_according_to_shape` will use
        # the new_shape of self._shape
        self._set_phi_and_psi_according_to_shape()

    @property
    def L(self):
        return self._L

    @property
    def Ts(self):
        return self._Ts

    @property
    def Fd(self):
        return self._Fd

    def _set_phi_and_psi_according_to_shape(self):
        """
        This will update the phi and psi attributes used to generate the
        jakes samples to reflect the current value of self._shape.
        """
        if self.shape is None:
            # The dimension of phi_l and psi_l will be L x 1. We set the
            #  last dimensions as 1, instead of setting the dimension of
            #  phi_l and psi_l simply as (L,), because it will be
            # broadcasted later by numpy when we multiply with the time.
            self._phi_l = 2 * np.pi * self.RS.rand(self.L, 1)
            self._psi_l = 2 * np.pi * self.RS.rand(self.L, 1)
        else:
            # The dimension of phi_l and psi_l will be L x Shape x 1. We
            #  set the last dimensions as 1, instead of setting the
            # dimension of phi_l and psi_l simply as (L,), because it
            # will be broadcasted later by numpy when we multiply with
            # the time.
            new_shape = [self.L]
            new_shape.extend(self.shape)
            new_shape.append(1)
            self._phi_l = 2 * np.pi * self.RS.rand(*new_shape)
            self._psi_l = 2 * np.pi * self.RS.rand(*new_shape)

    def _generate_time_samples(self, num_samples=None):
        """
        Generate the time samples that will be used internally in
        `generate_more_samples` method.

        Parameters
        ----------
        num_samples : int, optional
            Number of samples to be generated.

        Returns
        -------
        np.ndarray
            The numpy array with the time samples. The shape of the
            generated time variable is "(1, A, num_samples)", where 'A' has
            as many '1's as the length of self._shape.
            Ex: If self._shape is None then the shape of the returned 't'
            variable is (1, num_samples). If self._shape is (2,3) then the
            shape of the returned 't' variable is (1, 1, 1, num_samples)

        Notes
        -----
        Each time `_generate_time_samples` is called it will update
        `_current_time` to reflect the advance of the time after
        generating the new samples.
        """
        if num_samples is None:
            num_samples = 1

        # Generate a 1D numpy with the time samples
        t = np.arange(
            self._current_time,  # Start time
            num_samples * self.Ts + self._current_time,
            self.Ts * 1.0000000001)

        # Update the self._current_time variable with the value of the next
        # time sample that should be generated when _generate_time_samples
        # is called again.
        self._current_time = t[-1] + self.Ts

        # Now we will change the shape of the 't' variable to an
        # appropriated shape for later use.
        if self._shape is not None:
            # Ex: If self._shape is (2,3) then the shape of the generated
            # 't' variable should be (1,1,1,num_samples). The first
            # dimension correspond to the number of taps (that is, self.L),
            # the following two dimensions correspond to the dimensions in
            # self._shape, and the last dimension corresponds to the number
            # of time samples.
            #
            # Note that we use '1' for all dimensions except the last one
            # and numpy will replicate to the correct value later thanks to
            # broadcast.
            t.shape = [1] * (len(self._shape) + 1) + [int(num_samples)]
        else:
            # Since self._shape is None, we only need one dimension for the
            # taps (that is, self.L) and another dimension for the actual
            # time samples.
            #
            # Note that we use '1' for all dimensions except the last one
            # and numpy will replicate to the correct value later thanks to
            # broadcast.
            t.shape = (1, num_samples)

        return t

    def generate_more_samples(self, num_samples=None):
        """
        Generate next samples.

        Note that any subsequent call to this method continues from the
        point where the last call stopped. That is, if you generate 10
        samples and then 15 more samples, you will get the same samples you
        would have got if you had generated 25 samples.

        Parameters
        ----------
        num_samples : int, optional
            Number of samples (with the provided shape) to generate. If not
            provided it will be assumed to be 1.

        Notes
        -----
        This method will update the self._current_time variable.
        """
        # This method will also update the _current_time member variable
        t = self._generate_time_samples(num_samples)

        # Finally calculate the channel samples
        # noinspection PyTypeChecker
        h = (math.sqrt(1.0 / self.L) *
             np.sum(np.exp(1j * (2 * np.pi * self.Fd *
                                 np.cos(self._phi_l) * t + self._psi_l)),
                    axis=0))
        self._samples = h

    def skip_samples_for_next_generation(self, num_samples):
        """
        Advance sample generation process by `num_samples` similarly to
        what would happen if you call `generate_more_samples(
        num_samples=num_samples)`, but without actually generating the
        samples.

        This has the effect of advancing the internal time using by
        JakesSampleGenerator without generating any samples.

        Parameters
        ----------
        num_samples : int
            How many samples to skip.
        """
        self._current_time += num_samples * self.Ts

    def get_similar_fading_generator(self):
        """
        Get a similar fading generator with the same configuration,
        but that generates independent samples.

        Returns
        -------
        JakesSampleGenerator
            Another JakesSampleGenerator object with the same configuration
            of this object.
        """
        return JakesSampleGenerator(
            self._Fd, self._Ts, self._L, self._shape)
