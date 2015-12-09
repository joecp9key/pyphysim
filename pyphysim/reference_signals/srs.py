#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Module with Sounding Reference Signal (SRS) related functions"""

import numpy as np

from .zadoffchu import get_shifted_root_seq
from .root_sequence import RootSequence

__all__ = ['get_shifted_srs_seq', 'SrsUeSequence', 'SrsChannelEstimator']


# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxx Module Functions xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
def get_shifted_srs_seq(root_seq, n_cs):
    """
    Get the shifted root sequence suitable as the SRS sequence of a user.

    Parameters
    ----------
    root_seq : complex numpy array
        The root sequence to shift.
    n_cs : int
        The desired cyclic shift number. This should be an integer from 0
        to 7, where 0 will just return the base sequence, 1 gives the first
        shift, and so on.

    Returns
    -------
    numpy array
        The shifted root sequence.

    See Also
    --------
    get_shifted_root_seq, get_shifted_dmrs_seq
    """
    return get_shifted_root_seq(root_seq, n_cs, 8)


# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxx Classes xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
class SrsUeSequence(object):
    """
    SRS sequence of a single user.

    Parameters
    ----------
    n_cs : int
        The shift index of the user. This can be an integer from 1 to 8.
    root_seq : RootSequence object
        The SRS root sequence of the base station the user is
        associated to. This should be an object of the RootSequence
        class.
    """

    def __init__(self, n_cs, root_seq):
        root_seq_array = root_seq.seq_array()
        self._user_seq_array = get_shifted_srs_seq(root_seq_array, n_cs)
        self._n_cs = n_cs
        self._root_index = root_seq.index

    @property
    def size(self):
        """
        Return the size of the user's SRS sequence.

        Returns
        -------
        size : int
            The size of the user's SRS sequence.

        Example
        -------
        >>> root_seq1 = RootSequence(root_index=25, Nzc=139)
        >>> user_seq1 = SrsUeSequence(3, root_seq1)
        >>> user_seq1.size
        139
        >>> root_seq2 = RootSequence(root_index=25, Nzc=139, extend_to=150)
        >>> user_seq2 = SrsUeSequence(3, root_seq2)
        >>> user_seq2.size
        150
        """
        return self._user_seq_array.size

    def seq_array(self):
        """
        Get the user's SRS sequence as a numpy array.

        Returns
        -------
        seq : numpy array
            The user's SRS sequence.
        """
        return self._user_seq_array

    def __repr__(self):
        return "<SrsUeSequence(n_cs={0},root_index={1})>".format(
            self._n_cs, self._root_index)

    # xxxxxxxxxx Define some basic methods xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    # We can always just get the equivalent numpy array and perform the
    # operations on it, but having these operations defined here is
    # convenient
    def __add__(self, other):  # pragma: no cover
        """Perform addition with `other`"""
        return self.seq_array() + other

    def __radd__(self, other):  # pragma: no cover
        """Perform addition with `other`"""
        return self.seq_array() + other

    def __mul__(self, other):  # pragma: no cover
        """Perform multiplication with `other`"""
        return self.seq_array() * other

    def __rmul__(self, other):  # pragma: no cover
        """Perform multiplication with `other`"""
        return self.seq_array() * other

    def conjugate(self):  # pragma: no cover
        return self.seq_array().conj()

    def conj(self):  # pragma: no cover
        return self.seq_array().conj()
    # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


class SrsChannelEstimator(object):
    """
    Estimated the (uplink) channel based on the SRS sequence sent by one
    user.

    The estimation is performed according to the paper [Bertrand2011]_,
    where the received signal in the FREQUENCY DOMAIN is used by the
    estimator.

    Parameters
    ----------
    srs_ue : SrsUeSequence object
        The user's SRS sequence.

    Notes
    -----

    .. [Bertrand2011] Bertrand, Pierre, "Channel Gain Estimation from
       Sounding Reference Signal in LTE," Conference: Proceedings of the
       73rd IEEE Vehicular Technology Conference.
    """

    def __init__(self, srs_ue):
        self._srs_ue = srs_ue

    @property
    def ue_srs_seq(self):
        return self._srs_ue

    def estimate_channel_freq_domain(self, received_signal,
                                     num_taps_to_keep):
        """
        Estimate the channel based on the received signal.

        Parameters
        ----------
        received_signal : numpy array

            The received SRS signal after being transmitted through the
            channel (in the frequency domain). If this is a 2D numpy array
            the first dimensions is assumed to be "receive antennas" while
            the second dimension are the received requence elements.
        num_taps_to_keep : int
            Number of taps (in delay domain) to keep. All taps from 0 to
            `num_taps_to_keep`-1 will be kept and all other taps will be
            zeroed before applying the FFT to get the channel response in
            the frequency domain.

        Returns
        -------
        freq_response : numpy array
            The channel frequency response. Note that this will have twice
            as many elements as the sent SRS signal, since the SRS signal
            is sent every other subcarrier.
        """
        # User's SRS sequence
        r = self._srs_ue.seq_array()

        if received_signal.ndim == 1:
            # First we multiply (elementwise) the received signal by the
            # conjugate of the user's SRS sequence
            y = np.fft.ifft(np.conj(r) * received_signal, r.size)

            # The channel impulse response consists of the first
            # `num_taps_to_keep` elements in `y`.
            tilde_h = y[0:num_taps_to_keep]
        elif received_signal.ndim == 2:
            # Case with multiple receive antennas
            y = np.fft.ifft(np.conj(r)[np.newaxis, :] * received_signal, r.size)

            # The channel impulse response consists of the first
            # `num_taps_to_keep` elements in `y`.
            tilde_h = y[:, 0:num_taps_to_keep]
        else:
            ValueError("received_signal must have either one dimension (one "
                       "receive antenna) or two dimensions (first dimension "
                       "being the receive antenna dimension).")

        # Now we can apply the FFT to get the frequency response.
        # The number of subcarriers is twice the number of elements in the
        # SRS sequence due to the comb pattern
        Nsc = r.size
        tilde_H = np.fft.fft(tilde_h, 2 * Nsc)

        return tilde_H