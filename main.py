import json
from itertools import permutations



#---------------------------------------------------------------------------------
# The below function feeds the JSON input data into a convenient format
def extractJsonData(data_str: str) -> str:
    startIndex = data_str.find('[{')
    endIndex = data_str.rfind('}]') + 2
    if startIndex >= 0 and endIndex > startIndex:
        return data_str[startIndex:endIndex]
    return data_str


with open("data_99_items.json", "r") as f:
    raw_data = f.read()
    
extracted_json = extractJsonData(raw_data)
data = json.loads(extracted_json)

#---------------------------------------------------------------------------------
# Main Logic

class Cuboid:
    def __init__(self, x, y, z, l, w, h, supported_by=None, max_weight_capacity=float('inf')):
        self.x = x
        self.y = y
        self.z = z
        self.l = l
        self.w = w
        self.h = h
        self.supported_by = supported_by  # The item(s) this cuboid is supported by
        self.max_weight_capacity = max_weight_capacity  # Maximum weight this cuboid can support


class Item:
    def __init__(self, count_id, l, w, h, weight, fragility=1.0):
        self.count_id = count_id
        self.l = l
        self.w = w
        self.h = h
        self.weight = weight
        self.fragility = fragility  # Scale from 0 to 1, 0 being extremely fragile
        # Calculate weight per area as an indicator of how much weight the item can support
        self.weight_bearing_capacity = weight / (l * w) * fragility * 10  # Simplified formula


class Truck:
    def __init__(self, number):
        self.number = number
        self.remaining_weight = 10000  # kg
        self.available_cuboids = [Cuboid(0, 0, 0, 14, 2.8, 2.8)]
        self.items = []
        self.item_objects = []  # Store actual Item objects for reference
        self.floor_items = []  # Items placed directly on the truck floor
        
    def update_supporting_items(self, new_item, x, y, z, l, w, h):
        """Update the weight capacity of supporting items"""
        # Check if the item is sitting on the floor
        if z == 0:
            self.floor_items.append(new_item)
            return
            
        # Find items that are supporting this item
        supporting_items = []
        for item in self.item_objects:
            item_x, item_y, item_z = item.x, item.y, item.z
            item_l, item_w, item_h = item.l, item.w, item.h
            
            # Check if this item is directly below the new item
            if (item_z + item_h == z and 
                max(x, item_x) < min(x + l, item_x + item_l) and 
                max(y, item_y) < min(y + w, item_y + item_w)):
                
                # Calculate overlap area
                overlap_l = min(x + l, item_x + item_l) - max(x, item_x)
                overlap_w = min(y + w, item_y + item_w) - max(y, item_y)
                overlap_area = overlap_l * overlap_w
                
                # Calculate proportion of support
                proportion = overlap_area / (l * w)
                supporting_items.append((item, proportion))
        
        # Set the supporting items
        new_item.supported_by = supporting_items


def load_items(json_data):
    items = []
    for item in json_data:
        if item['Type'] == 'Cylinder':
            radius = float(item['Radius']) / 100  # Convert cm to meters
            height = float(item['Height']) / 100
            l = 2 * radius
            w = 2 * radius
            h = height
        else:  # Assuming Box for all other types
            l = float(item['Length']) / 100
            w = float(item['Width']) / 100
            h = float(item['Height']) / 100
        
        weight = float(item['Weight'])
        
        # Set a fragility based on the type and weight-to-volume ratio
        # This is a simplification - in a real system you'd have actual fragility data
        volume = l * w * h
        density = weight / volume if volume > 0 else float('inf')
        fragility = min(1.0, max(0.2, 1.0 - (density / 1000)))  # Higher density items are less fragile
        
        count_id = item['Count_ID'] if 'Count_ID' in item else item['Count_Id']
        
        items.append(Item(count_id, l, w, h, weight, fragility))
    return items


def generate_rotations(dimensions):
    return list(set(permutations(dimensions)))


def can_support_weight(supporting_item, new_item_weight):
    """Check if an item can support the weight of a new item"""
    return supporting_item.weight_bearing_capacity >= new_item_weight


def check_stacking_validity(truck, new_item, x, y, z, l, w, h):
    """Check if placing an item at the specified position is valid from a stacking perspective"""
    # Items on the floor can always be placed (as long as they fit)
    if z == 0:
        return True
    
    # Find all items that would be beneath this item
    has_support = False
    total_support_proportion = 0
    for item in truck.item_objects:
        item_x, item_y, item_z = item.x, item.y, item.z
        item_l, item_w, item_h = item.l, item.w, item.h
        
        # Check if this item is directly below the new item
        if (item_z + item_h == z and 
            max(x, item_x) < min(x + l, item_x + item_l) and 
            max(y, item_y) < min(y + w, item_y + item_w)):
            
            # Calculate overlap area
            overlap_l = min(x + l, item_x + item_l) - max(x, item_x)
            overlap_w = min(y + w, item_y + item_w) - max(y, item_y)
            overlap_area = overlap_l * overlap_w
            
            # Calculate proportion of support
            proportion = overlap_area / (l * w)
            total_support_proportion += proportion
            
            # Check if this item can support the new item
            if not can_support_weight(item, new_item.weight * proportion):
                return False
            
            has_support = True
    
    # Ensure the item has enough support (at least 70% of its base)
    return has_support and total_support_proportion >= 0.7


# Load and sort items by weight (heaviest first) to ensure proper stacking
items = load_items(data)
items.sort(key=lambda x: (-x.weight, -(x.l * x.w * x.h)))

trucks = []
truck_count = 0

for item in items:
    count_id = item.count_id
    weight = item.weight
    dimensions = (item.l, item.w, item.h)
    rotations = generate_rotations(dimensions)
    valid_rotations = [rot for rot in rotations if rot[0] <= 14 and rot[1] <= 2.8 and rot[2] <= 2.8]
    
    if not valid_rotations:
        print(f"Item {count_id} cannot be placed due to size constraints.")
        continue

    placed = False
    
    # Try to place in existing trucks first
    for truck in trucks:
        if truck.remaining_weight < weight:
            continue
            
        # Sort available cuboids by z-coordinate (height) to place items at the lowest possible position
        sorted_cuboids = sorted(truck.available_cuboids, key=lambda c: c.z)
        
        for cuboid in sorted_cuboids[:]:
            for rot in valid_rotations:
                rl, rw, rh = rot
                if rl <= cuboid.l and rw <= cuboid.w and rh <= cuboid.h:
                    x, y, z = cuboid.x, cuboid.y, cuboid.z
                    
                    # Check if this placement follows stacking rules
                    if check_stacking_validity(truck, item, x, y, z, rl, rw, rh):
                        # Create an item object with position information
                        placed_item = Item(count_id, rl, rw, rh, weight, item.fragility)
                        placed_item.x, placed_item.y, placed_item.z = x, y, z
                        
                        truck.items.append({
                            'Count_ID': count_id,
                            'x': x,
                            'y': y,
                            'z': z,
                            'l': rl,
                            'w': rw,
                            'h': rh,
                            'weight': weight
                        })
                        
                        # Update the weight capacity of supporting items
                        truck.update_supporting_items(placed_item, x, y, z, rl, rw, rh)
                        
                        truck.item_objects.append(placed_item)
                        truck.remaining_weight -= weight
                        
                        # Create new available spaces
                        new_cuboids = []
                        
                        # Space to the right
                        if cuboid.l - rl > 0:
                            new_cuboids.append(Cuboid(x + rl, y, z, cuboid.l - rl, cuboid.w, cuboid.h))
                        
                        # Space to the back
                        if cuboid.w - rw > 0:
                            new_cuboids.append(Cuboid(x, y + rw, z, rl, cuboid.w - rw, cuboid.h))
                        
                        # Space above
                        if cuboid.h - rh > 0:
                            new_cuboids.append(Cuboid(x, y, z + rh, rl, rw, cuboid.h - rh))
                        
                        truck.available_cuboids.remove(cuboid)
                        truck.available_cuboids.extend(new_cuboids)
                        
                        placed = True
                        break
                        
            if placed:
                break
                
        if placed:
            break
            
    # If not placed in an existing truck, create a new one
    if not placed:
        truck_count += 1
        new_truck = Truck(truck_count)
        
        for rot in valid_rotations:
            rl, rw, rh = rot
            if rl <= 14 and rw <= 2.8 and rh <= 2.8:
                # Create an item object with position information
                placed_item = Item(count_id, rl, rw, rh, weight, item.fragility)
                placed_item.x, placed_item.y, placed_item.z = 0, 0, 0
                
                new_truck.items.append({
                    'Count_ID': count_id,
                    'x': 0,
                    'y': 0,
                    'z': 0,
                    'l': rl,
                    'w': rw,
                    'h': rh,
                    'weight': weight
                })
                
                new_truck.item_objects.append(placed_item)
                new_truck.floor_items.append(placed_item)  # This is a floor item
                new_truck.remaining_weight -= weight
                
                initial = new_truck.available_cuboids.pop(0)
                
                # Create new available spaces
                if initial.l - rl > 0:
                    new_truck.available_cuboids.append(Cuboid(rl, 0, 0, initial.l - rl, initial.w, initial.h))
                if initial.w - rw > 0:
                    new_truck.available_cuboids.append(Cuboid(0, rw, 0, rl, initial.w - rw, initial.h))
                if initial.h - rh > 0:
                    new_truck.available_cuboids.append(Cuboid(0, 0, rh, rl, rw, initial.h - rh))
                
                trucks.append(new_truck)
                placed = True
                break
                
        if not placed:
            print(f"Item {count_id} couldn't be placed in a new truck.")

# Generate output JSON
output = []
for truck in trucks:
    for item in truck.items:
        output.append({
            'Count_ID': item['Count_ID'],
            'TruckNumber': truck.number,
            'x': item['x'],
            'y': item['y'],
            'z': item['z'],
            'weight': item['weight']  # Include weight in output for verification
        })

# Add truck utilization statistics
truck_stats = []
for i, truck in enumerate(trucks, 1):
    total_weight = sum(item['weight'] for item in truck.items)
    weight_utilization = total_weight / 10000 * 100
    
    truck_stats.append({
        'TruckNumber': i,
        'ItemCount': len(truck.items),
        'TotalWeight': total_weight,
        'WeightUtilization': f"{weight_utilization:.2f}%",
        'RemainingCapacity': truck.remaining_weight
    })

# Add stats to output
output_with_stats = {
    'Items': output,
    'TruckStats': truck_stats,
    'TotalTrucks': len(trucks)
}

json_string = json.dumps(output_with_stats, indent=4)




# Write the JSON string to a .json file
file_path = "output.json"
with open(file_path, "w") as json_file:
    json_file.write(json_string)

print(f"JSON data has been written to {file_path}")
print(f"Total trucks used: {len(trucks)}")
print(output_with_stats)