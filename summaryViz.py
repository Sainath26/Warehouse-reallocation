import json
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.gridspec import GridSpec
from matplotlib.colors import LinearSegmentedColormap

def visualizeTrucks(jsonFile):
    # Load JSON data
    with open(jsonFile, 'r') as f:
        data = json.load(f)
    
    # Group items by truck number
    trucks = {}
    for item in data:
        truckNum = item['TruckNumber']
        if truckNum not in trucks:
            trucks[truckNum] = []
        trucks[truckNum].append(item)
    
    # Create main figure
    nTrucks = len(trucks)
    cols = 4
    rows = int(np.ceil(nTrucks/cols))
    
    fig = plt.figure(figsize=(20, 10))
    gs = GridSpec(rows + 1, cols, height_ratios=[1]*rows + [0.1])
    
    # Create custom red-white colormap
    colors = [(1, 0, 0), (1, 1, 1)]  # Red to White
    cmap = LinearSegmentedColormap.from_list('RedWhite', colors)
    
    # Create color axis at bottom
    cax = fig.add_subplot(gs[rows, :])
    
    # Get all weights for normalization
    allWeights = [item['weight'] for truck in trucks.values() for item in truck]
    minWeight = min(allWeights)
    maxWeight = max(allWeights)
    norm = plt.Normalize(minWeight, maxWeight)
    
    # Create colorbar
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap.reversed()),
                     cax=cax, orientation='horizontal')
    cb.set_ticks([minWeight, maxWeight])
    cb.set_ticklabels([f"{minWeight:.1f}", f"{maxWeight:.1f}"])
    cb.set_label('Item Weight (kg) - Heaviest (Red) to Lightest (White)', fontsize=12)
    
    # Truck volume calculation
    truckVolume = 14 * 2.8 * 2.8
    
    # Plot trucks
    for idx, (truckNum, items) in enumerate(trucks.items()):
        ax = fig.add_subplot(gs[idx//cols, idx%cols], projection='3d')
        
        # Calculate packing efficiency
        totalItemVolume = sum(item['volume'] for item in items)
        packingEfficiency = (totalItemVolume / truckVolume) * 100
        
        ax.set_box_aspect([14, 2.8, 2.8])
        ax.set_xlim(0, 14)
        ax.set_ylim(0, 2.8)
        ax.set_zlim(0, 2.8)
        ax.set_title(f'Truck {truckNum}\nEfficiency: {packingEfficiency:.2f}%', fontsize=10)
        
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_zticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_zticklabels([])
        
        for item in items:
            dx = item['length']
            dy = item['width']
            dz = item['height']
            x = item['x']
            y = item['y']
            z = item['z']
            
            color = cmap.reversed()(norm(item['weight']))
            
            ax.bar3d(x, y, z, dx, dy, dz,
                     color=color,
                     alpha=0.8,
                     edgecolor='k',
                     linewidth=0.3,
                     shade=True)
        
        ax.view_init(elev=20, azim=-45)
    
    plt.tight_layout()
    plt.show()

# Usage
visualizeTrucks("output.json")