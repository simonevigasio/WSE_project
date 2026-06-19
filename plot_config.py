import matplotlib.pyplot as plt
import seaborn as sns

# Centralized plot configuration
font_settings = {
    'font.size': 14,
    'axes.titlesize': 16,
    'axes.labelsize': 14,
    'xtick.labelsize': 12,
    'ytick.labelsize': 20,
    'legend.fontsize': 12
}

def apply_plot_config():
    """Apply consistent font and context settings for plots."""
    plt.rcParams.update(font_settings)
    try:
        sns.set_context('notebook', rc=font_settings)
    except Exception:
        # If seaborn is not available or fails, silently continue using rcParams
        pass