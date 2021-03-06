from __future__ import print_function
import sys
import numpy as np
import fitsio
import tqdm

SHEARS = ['1p', '1m', '2p', '2m']


def _msk_it(d, s2n_cut=None, size_cut=None, shear=''):
    test_col = 'mcal_T_r' + shear
    if test_col in d.dtype.names:
        return (
            # (d['flags'] == 0) &
            # (np.sum(d['psf_flags'], axis=1) == 0) &
            # (d['obj_flags'] == 0) &
            # (d['gauss_flags'] == 0) &
            (d['mcal_flags'] == 0) &
            (d['mcal_s2n_r' + shear] > s2n_cut) &
            ((d['mcal_T_r' + shear] / d['mcal_Tpsf']) > size_cut)
        )
    else:
        return (
            # (d['flags'] == 0) &
            # (np.sum(d['psf_flags'], axis=1) == 0) &
            # (d['obj_flags'] == 0) &
            # (d['gauss_flags'] == 0) &
            (d['mcal_flags'] == 0) &
            (d['mcal_s2n' + shear] > s2n_cut) &
            (d['mcal_T_ratio' + shear] > size_cut)
        )


def _measure_R(d, s2n_cut=None, size_cut=None):
    msks = {}
    for shear in SHEARS:
        msks[shear] = _msk_it(
            d, s2n_cut=s2n_cut, size_cut=size_cut, shear='_' + shear)

    if 'mcal_g' in d.dtype.names:
        msks['noshear'] = _msk_it(
            d, s2n_cut=s2n_cut, size_cut=size_cut, shear='')
    else:
        msks['noshear'] = _msk_it(
            d, s2n_cut=s2n_cut, size_cut=size_cut, shear='_noshear')

    g1_1p = np.mean(d['mcal_g_1p'][msks['1p'], 0])
    g1_1m = np.mean(d['mcal_g_1m'][msks['1m'], 0])
    g2_2p = np.mean(d['mcal_g_2p'][msks['2p'], 1])
    g2_2m = np.mean(d['mcal_g_2m'][msks['2m'], 1])
    R11 = (g1_1p - g1_1m) / 2 / 0.01
    R22 = (g2_2p - g2_2m) / 2 / 0.01

    if 'mcal_g' in d.dtype.names:
        g1 = np.mean(d['mcal_g'][msks['noshear'], 0])
        g2 = np.mean(d['mcal_g'][msks['noshear'], 1])
    else:
        g1 = np.mean(d['mcal_g_noshear'][msks['noshear'], 0])
        g2 = np.mean(d['mcal_g_noshear'][msks['noshear'], 1])

    return g1, g2, R11, R22


fnames = sys.argv[1:]

d = []
for fname in sorted(fnames):
    _d = fitsio.read(fname)
    d.extend(list(_d))
d = np.array(d, dtype=_d.dtype)
n_obj = len(d)

s2n_cut = 10.0
size_cut = 0.5

n_jack = 100
if n_jack > n_obj:
    n_jack = n_obj // 10

marr = []
carr = []
rng = np.random.RandomState(seed=10)
n_per_sample = n_obj // n_jack
sinds = np.argsort(rng.uniform(size=n_obj))
msk = np.ones(n_obj, dtype=np.bool)
loc = 0
for _ in tqdm.trange(n_jack):
    msk[:] = True
    msk[sinds[loc:loc+n_per_sample]] = False
    g1, g2, R11, R22 = _measure_R(d[msk], s2n_cut=s2n_cut, size_cut=size_cut)
    marr.append(g1/R11 / 0.02 - 1.0)
    carr.append(g2/R22)
    loc += n_per_sample

marr = np.array(marr)
carr = np.array(carr)

m = np.mean(marr)
c = np.mean(carr)
m_err = np.sqrt((n_jack - 1)/n_jack * np.sum((marr - m)**2))
c_err = np.sqrt((n_jack - 1)/n_jack * np.sum((carr - c)**2))

print('nobj:', n_obj)
print('njack:', n_jack)
if np.abs(m) > 0.01:
    print("m: %f +/- %f" % (m, m_err))
    print("c: %f +/- %f" % (c, c_err))
else:
    print("m [1e-3]: %f +/- %f" % (m/1e-3, m_err/1e-3))
    print("c [1e-4]: %f +/- %f" % (c/1e-4, c_err/1e-4))
