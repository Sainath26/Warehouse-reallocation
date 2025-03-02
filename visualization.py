import json
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.colors as mcolors
import random

def generate_colors(num_trucks):
    """Generate distinct colors for each truck"""
    base_colors = list(mcolors.TABLEAU_COLORS.values())
    if num_trucks <= len(base_colors):
        return base_colors[:num_trucks]    
    return [f"#{random.randint(0, 0xFFFFFF):06x}" for _ in range(num_trucks)]

def plot_truck(ax, truck_length, truck_width, truck_height, alpha=0.1):
    """Plot the truck container as a wireframe"""
    # Truck coordinates (converted from meters to cm)
    x = [0, truck_length, truck_length, 0, 0]
    y = [0, 0, truck_width, truck_width, 0]
    z = [0, 0, 0, 0, 0]
    
    ax.plot(x, y, z, color='black', alpha=0.5)
    ax.plot(x, y, [truck_height]*5, color='black', alpha=0.5)
    
    for i in range(4):
        ax.plot([x[i], x[i]], [y[i], y[i]], [0, truck_height], color='black', alpha=0.5)
    
    vertices = np.array([
        [(0, 0, 0), (truck_length, 0, 0), (truck_length, truck_width, 0), (0, truck_width, 0)],
        [(0, 0, truck_height), (truck_length, 0, truck_height), 
         (truck_length, truck_width, truck_height), (0, truck_width, truck_height)],
        [(0, 0, 0), (truck_length, 0, 0), (truck_length, 0, truck_height), (0, 0, truck_height)],
        [(truck_length, 0, 0), (truck_length, truck_width, 0), 
         (truck_length, truck_width, truck_height), (truck_length, 0, truck_height)],
        [(truck_length, truck_width, 0), (0, truck_width, 0), 
         (0, truck_width, truck_height), (truck_length, truck_width, truck_height)],
        [(0, truck_width, 0), (0, 0, 0), (0, 0, truck_height), (0, truck_width, truck_height)]
    ])
    
    truck_container = Poly3DCollection(vertices, alpha=alpha, facecolor='gray', edgecolor='black')
    ax.add_collection3d(truck_container)

def plot_cuboid(ax, x, y, z, dx, dy, dz, color='blue', alpha=0.5):
    """Plot a cuboid item with specified dimensions"""
    vertices = np.array([
        [x, y, z],
        [x+dx, y, z],
        [x+dx, y+dy, z],
        [x, y+dy, z],
        [x, y, z+dz],
        [x+dx, y, z+dz],
        [x+dx, y+dy, z+dz],
        [x, y+dy, z+dz]
    ])
    
    faces = [
        [vertices[0], vertices[1], vertices[2], vertices[3]],
        [vertices[4], vertices[5], vertices[6], vertices[7]],
        [vertices[0], vertices[1], vertices[5], vertices[4]],
        [vertices[2], vertices[3], vertices[7], vertices[6]],
        [vertices[0], vertices[3], vertices[7], vertices[4]],
        [vertices[1], vertices[2], vertices[6], vertices[5]]
    ]
    
    cuboid = Poly3DCollection(faces, alpha=alpha, facecolor=color, edgecolor='black', linewidth=0.3)
    ax.add_collection3d(cuboid)

def visualize_truck_loading(loading_data, truck_dimensions=(1400, 280, 280)):
    """Create a 3D visualization of truck loading"""
    items = loading_data["Items"]
    total_trucks = loading_data["TotalTrucks"]
    colors = generate_colors(total_trucks)
    
    # Group items by truck
    trucks_items = {}
    for item in items:
        truck_num = item["TruckNumber"]
        if truck_num not in trucks_items:
            trucks_items[truck_num] = []
        trucks_items[truck_num].append(item)
    
    fig = plt.figure(figsize=(15, 7))
    
    for i, (truck_num, truck_items) in enumerate(sorted(trucks_items.items())):
        ax = fig.add_subplot(1, len(trucks_items), i+1, projection='3d')
        
        # Get truck stats for title
        truck_stat = next(ts for ts in loading_data["TruckStats"] if ts["TruckNumber"] == truck_num)
        ax.set_title(
            f'Truck {truck_num}\n'
            f'Items: {truck_stat["ItemCount"]}, '
            f'Total Weight: {truck_stat["TotalWeight"]} kg\n'
            f'Utilization: {truck_stat["WeightUtilization"]}'
        )
        
        ax.set_xlabel('Length (cm)')
        ax.set_ylabel('Width (cm)')
        ax.set_zlabel('Height (cm)')
        
        plot_truck(ax, *truck_dimensions)
        
        # Plot items as cuboids
        for item in truck_items:
            # Convert coordinates from meters to cm
            x = item["x"] * 100
            y = item["y"] * 100
            z = item["z"] * 100
            
            # Use fixed size (10x10x10 cm cubes)
            plot_cuboid(
                ax, x, y, z,
                dx=10, dy=10, dz=10,
                color=colors[truck_num-1],
                alpha=0.7
            )
        
        ax.set_xlim(0, truck_dimensions[0])
        ax.set_ylim(0, truck_dimensions[1])
        ax.set_zlim(0, truck_dimensions[2])
        ax.set_box_aspect([
            truck_dimensions[0]/max(truck_dimensions),
            truck_dimensions[1]/max(truck_dimensions),
            truck_dimensions[2]/max(truck_dimensions)
        ])
    
    plt.tight_layout()
    plt.savefig("truck_loading_visualization.png", dpi=300, bbox_inches='tight')
    plt.show()

def main():
    with open("output.json", "r") as f:
        loading_data = json.load(f)
    
    visualize_truck_loading(loading_data)
    print(f"Visualization complete. Total trucks: {loading_data['TotalTrucks']}")

if __name__ == "__main__":
    main()