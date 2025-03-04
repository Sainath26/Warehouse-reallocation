""" 
Loading necessary packages 
"""
import json
from itertools import permutations



""" 
This function is used to get the raw data from raw file and store it as a list
"""
def extractJsonData(jsonFile):
    with open(jsonFile, "r") as f:
        dataStr = f.read()
    
    startIndex = dataStr.find('[{')
    endIndex = dataStr.rfind('}]') + 2
    if startIndex >= 0 and endIndex > startIndex:
        jsonStr = dataStr[startIndex:endIndex]
        return json.loads(jsonStr)  
    return json.loads(dataStr)  


data = extractJsonData("warehouse-reallocation/data_999_items.json")


""" 
This class is used to model 3d rectangular place within the truck that can be used to place the items.
 The main purpose of this class is to manage the space within the truck.
"""
class Cuboid:
    def __init__(self, x, y, z, l, w, h, supportedBy=None, maxWeightCapacity=float('inf')):
        self.x = x
        self.y = y
        self.z = z
        self.l = l
        self.w = w
        self.h = h
        self.supportedBy = supportedBy
        self.maxWeightCapacity = maxWeightCapacity


""" 
This class is used to represent the physical items that needs to be placed inside the truck.
It focuses on the properties and constraints of the items:
primiary key: countId
dimension
weight
fragility
Weight-Bearing Capacity 
"""
class Item:
    def __init__(self, countId, l, w, h, weight, fragility=1.0):
        self.countId = countId
        self.l = l
        self.w = w
        self.h = h
        self.weight = weight
        self.fragility = fragility
        self.weightBearingCapacity = weight / (l * w) * fragility * 10

""" 
This class is the core component of the algorithm. This class is used to model the truck and manage trucks used for packing items
Key Purposes:
- Represent a truck
- Track available space
- Manage weight capacity
- Handle stacking
- Update space dynamically
- Enforce stacking constraints
"""
class Truck:
    def __init__(self, number):
        self.number = number
        self.remainingWeight = 10000
        self.availableCuboids = [Cuboid(0, 0, 0, 14, 2.8, 2.8)]
        self.items = []
        self.itemObjects = []
        self.floorItems = []
    

    """ 
    This function is responsible for determining which items support a newly placed items and updata
    the supportedBy attribute of the new item accordingly
    """
    def updateSupportingItems(self, newItem, x, y, z, l, w, h):
        if z == 0:
            self.floorItems.append(newItem)
            return
        
        supportingItems = []
        for item in self.itemObjects:
            itemX, itemY, itemZ = item.x, item.y, item.z
            itemL, itemW, itemH = item.l, item.w, item.h
            
            if (itemZ + itemH == z and 
                max(x, itemX) < min(x + l, itemX + itemL) and 
                max(y, itemY) < min(y + w, itemY + itemW)):
                
                overlapL = min(x + l, itemX + itemL) - max(x, itemX)
                overlapW = min(y + w, itemY + itemW) - max(y, itemY)
                overlapArea = overlapL * overlapW
                proportion = overlapArea / (l * w)
                supportingItems.append((item, proportion))
        
        newItem.supportedBy = supportingItems


""" 
This function is used to process the json data and convert it into a list of Item(custom class) objects
"""
def loadItems(jsonData):
    items = []
    for item in jsonData:
        if item['Type'] == 'Cylinder':
            radius = float(item['Radius']) / 100
            height = float(item['Height']) / 100
            l = 2 * radius
            w = 2 * radius
            h = height
        else:
            l = float(item['Length']) / 100
            w = float(item['Width']) / 100
            h = float(item['Height']) / 100
        
        weight = float(item['Weight'])
        volume = l * w * h
        density = weight / volume if volume > 0 else float('inf')
        fragility = min(1.0, max(0.2, 1.0 - (density / 1000)))
        countId = item['Count_ID'] if 'Count_ID' in item else item['Count_Id']
        items.append(Item(countId, l, w, h, weight, fragility))
    return items

""" 
This function is used to generate all possible rotations of the item
"""
def generateRotations(dimensions):
    return list(set(permutations(dimensions)))

""" 
This function checks if the supporting item can support the weight of the new item
"""
def canSupportWeight(supportingItem, newItemWeight):
    return supportingItem.weightBearingCapacity >= newItemWeight


""" 
This function checks if the stacking is valid
"""
def checkStackingValidity(truck, newItem, x, y, z, l, w, h):
    if z == 0:
        return True
    
    hasSupport = False
    totalSupportProportion = 0
    for item in truck.itemObjects:
        itemX, itemY, itemZ = item.x, item.y, item.z
        itemL, itemW, itemH = item.l, item.w, item.h
        
        if (itemZ + itemH == z and 
            max(x, itemX) < min(x + l, itemX + itemL) and 
            max(y, itemY) < min(y + w, itemY + itemW)):
            
            overlapL = min(x + l, itemX + itemL) - max(x, itemX)
            overlapW = min(y + w, itemY + itemW) - max(y, itemY)
            overlapArea = overlapL * overlapW
            proportion = overlapArea / (l * w)
            totalSupportProportion += proportion
            
            if not canSupportWeight(item, newItem.weight * proportion):
                return False
            
            hasSupport = True
    
    return hasSupport and totalSupportProportion >= 0.7

items = loadItems(data)
items.sort(key=lambda x: (-x.weight, -(x.l * x.w * x.h)))

trucks = []
truckCount = 0



""" 
The main 3d-binning algorithm is implemented below 
"""
for item in items:
    countId = item.countId
    weight = item.weight
    dimensions = (item.l, item.w, item.h)
    rotations = generateRotations(dimensions)
    validRotations = [rot for rot in rotations if rot[0] <= 14 and rot[1] <= 2.8 and rot[2] <= 2.8]
    
    if not validRotations:
        print(f"Item {countId} cannot be placed due to size constraints.")
        continue

    placed = False
    
    for truck in trucks:
        if truck.remainingWeight < weight:
            continue
            
        sortedCuboids = sorted(truck.availableCuboids, key=lambda c: c.z)
        
        for cuboid in sortedCuboids[:]:
            for rot in validRotations:
                rl, rw, rh = rot
                if rl <= cuboid.l and rw <= cuboid.w and rh <= cuboid.h:
                    x, y, z = cuboid.x, cuboid.y, cuboid.z
                    
                    if checkStackingValidity(truck, item, x, y, z, rl, rw, rh):
                        placedItem = Item(countId, rl, rw, rh, weight, item.fragility)
                        placedItem.x, placedItem.y, placedItem.z = x, y, z
                        
                        truck.items.append({
                            'Count_ID': countId,
                            'x': x,
                            'y': y,
                            'z': z,
                            'l': rl,
                            'w': rw,
                            'h': rh,
                            'weight': weight,
                            'volume': rl * rw * rh
                        })
                        
                        truck.updateSupportingItems(placedItem, x, y, z, rl, rw, rh)
                        truck.itemObjects.append(placedItem)
                        truck.remainingWeight -= weight
                        
                        newCuboids = []
                        if cuboid.l - rl > 0:
                            newCuboids.append(Cuboid(x + rl, y, z, cuboid.l - rl, cuboid.w, cuboid.h))
                        if cuboid.w - rw > 0:
                            newCuboids.append(Cuboid(x, y + rw, z, rl, cuboid.w - rw, cuboid.h))
                        if cuboid.h - rh > 0:
                            newCuboids.append(Cuboid(x, y, z + rh, rl, rw, cuboid.h - rh))
                        
                        truck.availableCuboids.remove(cuboid)
                        truck.availableCuboids.extend(newCuboids)
                        placed = True
                        break
            if placed:
                break
        if placed:
            break
            
    if not placed:
        truckCount += 1
        newTruck = Truck(truckCount)
        
        for rot in validRotations:
            rl, rw, rh = rot
            if rl <= 14 and rw <= 2.8 and rh <= 2.8:
                placedItem = Item(countId, rl, rw, rh, weight, item.fragility)
                placedItem.x, placedItem.y, placedItem.z = 0, 0, 0
                
                newTruck.items.append({
                    'Count_ID': countId,
                    'x': 0,
                    'y': 0,
                    'z': 0,
                    'l': rl,
                    'w': rw,
                    'h': rh,
                    'weight': weight,
                    'volume': rl * rw * rh
                })
                
                newTruck.itemObjects.append(placedItem)
                newTruck.floorItems.append(placedItem)
                newTruck.remainingWeight -= weight
                
                initial = newTruck.availableCuboids.pop(0)
                if initial.l - rl > 0:
                    newTruck.availableCuboids.append(Cuboid(rl, 0, 0, initial.l - rl, initial.w, initial.h))
                if initial.w - rw > 0:
                    newTruck.availableCuboids.append(Cuboid(0, rw, 0, rl, initial.w - rw, initial.h))
                if initial.h - rh > 0:
                    newTruck.availableCuboids.append(Cuboid(0, 0, rh, rl, rw, initial.h - rh))
                
                trucks.append(newTruck)
                placed = True
                break
                
        if not placed:
            print(f"Item {countId} couldn't be placed in a new truck.")




""" 
This part of the code is used to write the output to a json file
"""
output = []
for truck in trucks:
    for item in truck.items:
        output.append({
            'Count_ID': item['Count_ID'],
            'TruckNumber': truck.number,
            'x': item['x'],
            'y': item['y'],
            'z': item['z'],
            'weight': item['weight'],
            'length': item['l'],
            'width': item['w'],
            'height': item['h'],
            'volume': item['volume']
        })

jsonString = json.dumps(output, indent=4)

filePath = "warehouse-reallocation/output.json"
with open(filePath, "w") as jsonFile:
    jsonFile.write(jsonString)

print(f"JSON data has been written to {filePath}")
print(f"Total trucks used: {len(trucks)}")