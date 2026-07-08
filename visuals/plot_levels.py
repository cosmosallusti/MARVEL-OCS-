import matplotlib.pyplot as plt

OLD_FILE = "EnergyLevels_out.txt"     # original 622 data (Tennyson baseline)
NEW_FILE = "EnergyLevels__1_.txt"     # updated MARVEL run

def parse_levels(fn):
    """Format: v1 v2 v3 l J parity  energy  [unc  count]"""
    levels, plot_data = {}, []
    with open(fn) as f:
        for line in f:
            p = line.split()
            if len(p) < 7:
                continue
            try:
                v1,v2,v3,l,J = (int(p[0]),int(p[1]),int(p[2]),int(p[3]),int(p[4]))
                parity = p[5]; E = float(p[6])
            except ValueError:
                continue
            levels[(v1,v2,v3,l,J,parity)] = E
            plot_data.append((l, J, E))
    return levels, plot_data

old_levels, old_plot = parse_levels(OLD_FILE)
new_levels, new_plot = parse_levels(NEW_FILE)

added_keys   = set(new_levels) - set(old_levels)
removed_keys = set(old_levels) - set(new_levels)
new_only = [(l,J,E) for (v1,v2,v3,l,J,pa),E in new_levels.items()
            if (v1,v2,v3,l,J,pa) in added_keys]

print(f"Old levels : {len(old_levels)}")
print(f"New levels : {len(new_levels)}")
print(f"Added      : {len(new_only)}")
print(f"Removed    : {len(removed_keys)}")
print(f"Net change : {len(new_levels)-len(old_levels)}")

ell_colours = {0:"#1f3a93", 1:"#c0392b", 2:"#27ae60"}
NEW_COLOUR  = "#e67e22"

fig, ax = plt.subplots(figsize=(12,7))
for lv in sorted(ell_colours):                      # plot all levels, coloured by l
    js=[J for (l,J,E) in new_plot if l==lv]
    es=[E for (l,J,E) in new_plot if l==lv]
    ax.scatter(js, es, s=7, c=ell_colours[lv], marker="+",
               linewidths=0.5, zorder=2, label=rf"$\ell = {lv}$")

js_new=[J for (l,J,E) in new_only]; es_new=[E for (l,J,E) in new_only]
ax.scatter(js_new, es_new, s=34, marker="o", facecolors=NEW_COLOUR,
           edgecolors=NEW_COLOUR, linewidths=0.8, zorder=3, label="New levels")

ax.set_xlabel("J", fontsize=14)
ax.set_ylabel(r"Energy / cm$^{-1}$", fontsize=14)
ax.tick_params(labelsize=12)
ax.set_xlim(-2, None); ax.set_ylim(-200, None)
ax.legend(fontsize=11, loc="upper right", framealpha=0.9, markerscale=1.6)
fig.tight_layout()
fig.savefig("energy_levels_comparison.png", dpi=300, bbox_inches="tight")
fig.savefig("energy_levels_comparison.pdf", bbox_inches="tight")
print("\nplotted", len(js_new), "orange circles")
