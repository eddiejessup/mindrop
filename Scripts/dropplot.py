#! /usr/bin/env python

from __future__ import print_function
import argparse
import numpy as np
import matplotlib.pyplot as pp
# import ejm_rcparams
import droplyse


figsize = (7.5, 5.5)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot droplet analysis files')
    parser.add_argument('datnames', nargs='+',
                        help='Data files')
    args = parser.parse_args()

    fig_peak = pp.figure(figsize=figsize)
    ax_peak = fig_peak.gca()
    fig_nf = pp.figure(figsize=figsize)
    ax_nf = fig_nf.gca()
    fig_mean = pp.figure(figsize=figsize)
    ax_mean = fig_mean.gca()
    fig_var = pp.figure(figsize=figsize)
    ax_var = fig_var.gca()
    fig_eta = pp.figure(figsize=figsize)
    ax_eta = fig_eta.gca()

    ps = [('o', 'red', r'Experiment'),
          ('^', 'green', r'Simulation, $\theta_\mathrm{r}^\mathrm{(c)} = \pi$'),
          ('x', 'blue', r'Simulation, $\theta_\mathrm{r}^\mathrm{(c)} = 0$'),
          ]

    for i, datname in enumerate(args.datnames):
        (n, n_err, R_drop, r_mean, r_mean_err, r_var, r_var_err,
         R_peak, R_peak_err, n_peak, n_peak_err, hemisphere, theta_max) = np.loadtxt(datname, unpack=True, delimiter=' ')

        assert np.all(hemisphere == 1.0) or np.all(hemisphere == 0.0)
        hemisphere = hemisphere[0]
        assert np.all(theta_max == theta_max[0])
        theta_max = theta_max[0]

        rho_0 = droplyse.n0_to_rho0(
            n, R_drop, droplyse.dim, hemisphere, theta_max)
        rho_0_err = droplyse.n0_to_rho0(
            n_err, R_drop, droplyse.dim, hemisphere, theta_max)
        vf = rho_0 * droplyse.V_particle

        V_drop = droplyse.V_sector(R_drop, theta_max, hemisphere)

        V_peak = V_drop - droplyse.V_sector(R_peak, theta_max, hemisphere)
        rho_peak = n_peak / V_peak
        rho_peak_err = n_peak_err / V_peak

        f_peak = n_peak / n
        f_peak_err = f_peak * \
            np.sqrt((n_peak_err / n_peak) ** 2 + (n_err / n) ** 2)

        vf = rho_0 * droplyse.V_particle
        vf_err = rho_0_err * droplyse.V_particle
        vp = 100.0 * vf
        vp_err = 100.0 * vf_err

        eta = droplyse.n_to_eta(n_peak, R_drop, theta_max, hemisphere)
        eta_err = droplyse.n_to_eta(n_peak_err, R_drop, theta_max, hemisphere)
        eta_0 = droplyse.n_to_eta(n, R_drop, theta_max, hemisphere)
        eta_0_err = droplyse.n_to_eta(n_err, R_drop, theta_max, hemisphere)

        m, c, label = ps[i]
        # label = datname
        # label = label.replace('_', '\_')

        for e in zip(n, R_drop, vp, eta_0):
            print(*e)

        ax_peak.errorbar(vp, rho_peak / rho_0, yerr=rho_peak_err / rho_0,
                         xerr=vp_err, c=c, marker=m, label=label, ls='none', ms=5)
        ax_nf.errorbar(vp, f_peak, yerr=f_peak_err,
                       xerr=vp_err, c=c, marker=m, label=label, ls='none', ms=5)
        ax_eta.errorbar(eta_0, eta, yerr=eta_err,
                        xerr=eta_0_err, marker=m, label=label, c=c, ls='none', ms=5)
        ax_mean.errorbar(vp, r_mean, yerr=r_mean_err,
                         xerr=vp_err, c=c, marker=m, label=label, ls='none', ms=5)
        ax_var.errorbar(vp, r_var, yerr=r_var_err,
                        xerr=vp_err, c=c, marker=m, label=label, ls='none', ms=5)

    ax_peak.axhline(1.0, lw=2, c='cyan', ls='--', label='Uniform')
    ax_peak.set_xscale('log')
    ax_peak.set_xlabel(r'Volume fraction $\theta$ \. (\%)', fontsize=20)
    ax_peak.set_ylabel(r'$\rho_\mathrm{p} / \rho_0$', fontsize=20)
    ax_peak.legend(loc='lower left', fontsize=16)

    ax_nf.axhline(1.0, lw=2, c='magenta',
                  ls='--', label='Complete accumulation')
    ax_nf.set_xscale('log')
    ax_nf.set_xlabel(r'Volume fraction $\theta$ \. (\%)', fontsize=20)
    ax_nf.set_ylabel(r'$\mathrm{n_{peak} / n}$', fontsize=20)
    ax_nf.legend(loc='lower left', fontsize=16)

    x = np.logspace(-3, 1, 10)
    ax_eta.plot(x, x, lw=2, c='magenta',
                ls='--', label='Complete accumulation')
    ax_eta.set_xscale('log')
    ax_eta.set_yscale('log')
    ax_eta.set_xlabel(r'$\eta_0$', fontsize=20)
    ax_eta.set_ylabel(r'$\eta$', fontsize=20)
    ax_eta.legend(loc='lower right', fontsize=16)

    ax_mean.axhline(
        droplyse.dim / (droplyse.dim + 1.0), lw=2, c='cyan', ls='--', label='Uniform')
    ax_mean.axhline(1.0, lw=2, c='magenta',
                    ls='--', label='Complete accumulation')
    ax_mean.set_xscale('log')
    ax_mean.set_ylim(0.73, 1.025)
    ax_mean.set_xlabel(r'Volume fraction $\theta$ \. (\%)', fontsize=20)
    ax_mean.set_ylabel(r'$\langle r \rangle / \mathrm{R}$', fontsize=20)
    ax_mean.legend(loc='lower left', fontsize=16)

    ax_var.axhline(
        droplyse.dim *
        (1.0 / (droplyse.dim + 2.0) -
         droplyse.dim / (droplyse.dim + 1.0) ** 2),
        label='Uniform', lw=2, c='cyan', ls='--')
    ax_var.axhline(0.0, lw=2, c='magenta',
                   ls='--', label='Complete accumulation')
    ax_var.set_xscale('log')
    ax_var.set_xlabel(r'Volume fraction $\theta$ \. (\%)', fontsize=20)
    ax_var.set_ylabel(r'$\mathrm{Var} \left[ r \right] / R^2$', fontsize=20)
    ax_var.legend(loc='upper left', fontsize=16)

    pp.show()