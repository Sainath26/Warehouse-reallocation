import json
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

def visualize_trucks(json_file):
    # Load JSON data
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Group items by truck number
    trucks = {}
    for item in data:
        truck_num = item['TruckNumber']
        if truck_num not in trucks:
            trucks[truck_num] = []
        trucks[truck_num].append(item)
    
    # Visualize each truck
    for truck_num, items in trucks.items():
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Setting truck dimensions (14m x 2.8m x 2.8m)
        ax.set_xlim([0, 14])
        ax.set_ylim([0, 2.8])
        ax.set_zlim([0, 2.8])
        
        ax.set_xlabel('Length (m)')
        ax.set_ylabel('Width (m)')
        ax.set_zlabel('Height (m)')
        ax.set_title(f'Truck {truck_num} Loading Visualization')
        
        # Create color map based on item weights
        weights = [item['weight'] for item in items]
        colors = plt.cm.viridis(np.linspace(0, 1, len(weights)))
        
        for idx, item in enumerate(items):
            # Create cube dimensions
            dx = item['length']
            dy = item['width']
            dz = item['height']
            
            # Create cube position
            x = item['x']
            y = item['y']
            z = item['z']
            
            # Plot cube
            cube = ax.bar3d(x, y, z, dx, dy, dz, 
                            color=colors[idx], 
                            alpha=0.6, 
                            edgecolor='black',
                            linewidth=0.3)
            
            # Add text label
            ax.text(x + dx/2, y + dy/2, z + dz/2, 
                   item['Count_ID'], 
                   ha='center', va='center',
                   fontsize=6, color='black')
        
        # Create legend proxy
        proxy = [plt.Rectangle((0,0),1,1,fc=colors[idx]) 
                for idx in range(len(items))]
        plt.legend(proxy, [f"{item['Count_ID']} ({item['weight']}kg)" 
                          for item in items],
                  bbox_to_anchor=(1.05, 1), 
                  loc='upper left', 
                  title="Items (Weight)")
        
        plt.tight_layout()
        plt.show()

# Usage
visualize_trucks("warehouse-reallocation/output.json")