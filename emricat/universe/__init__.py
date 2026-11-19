"""
STEPS 4-5 -- Fill the Universe and draw the events (coordinators' proposal).

Step 4 (slides 12-13): each snapshot represents a comoving shell of the
Universe around LISA. Each simulated galaxy i is replicated

    N_i = n_i * Delta V_c,     n_i = 1/V_box (simulations) or w_i (SAMs)

times. On average this reproduces a light cone without building one.

Step 5 (slide 14): every replica gets its own nucleus, merger history and
EMRI draw (frequentist approach):

    expected EMRIs  lambda = Gamma * T_obs / (1+z)
    observed EMRIs  n ~ Poisson(lambda)          (usually 0, rarely 1)

Every success becomes a catalogue event. A detection criterion (SNR) is
still to be defined.

Modules
-------
replication.py  shells, number of replicas per galaxy, chunked replica generation
sampling.py     expected number of EMRIs, Poisson draw, event redshifts
detection.py    detection criterion (placeholder)
"""
