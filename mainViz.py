import json
import plotly.graph_objects as go
import plotly.express as px

def createCube(x, y, z, dx, dy, dz):
    """
    Generating the 8 vertices of a cube starting at (x, y, z)
    with dimensions (dx, dy, dz).
    """
    vX = [x, x+dx, x+dx, x, x, x+dx, x+dx, x]
    vY = [y, y, y+dy, y+dy, y, y, y+dy, y+dy]
    vZ = [z, z, z, z, z+dz, z+dz, z+dz, z+dz]
    return vX, vY, vZ

def visualizeTrucksPlotly(jsonFile):
    # Load JSON data
    with open(jsonFile, 'r') as f:
        data = json.load(f)
    
    # Group items by truck number
    trucks = {}
    for item in data:
        truckNum = item['TruckNumber']
        trucks.setdefault(truckNum, []).append(item)
    
    # Process each truck's data
    for truckNum, items in trucks.items():
        fig = go.Figure()
        nItems = len(items)
        
        for idx, item in enumerate(items):
            # Unpack item properties
            x0 = item['x']
            y0 = item['y']
            z0 = item['z']
            dx = item['length']
            dy = item['width']
            dz = item['height']
            
            # Generate cube vertices
            vX, vY, vZ = createCube(x0, y0, z0, dx, dy, dz)
            
            # Get a color from the Viridis colorscale based on the item's index
            normVal = idx / (nItems - 1) if nItems > 1 else 0.5
            color = px.colors.sample_colorscale("Viridis", normVal)[0]
            
            # Add the cube as a Mesh3d trace.
            # The following indices define triangles for the cube faces.
            fig.add_trace(go.Mesh3d(
                x=vX,
                y=vY,
                z=vZ,
                i=[0, 0, 4, 4, 0, 0, 3, 3, 0, 0, 1, 1],
                j=[1, 2, 5, 6, 1, 5, 2, 6, 3, 7, 2, 6],
                k=[2, 3, 6, 7, 5, 4, 6, 7, 7, 4, 6, 5],
                color=color,
                opacity=0.6,
                flatshading=True,
                name=f"{item['Count_ID']} ({item['weight']}kg)"
            ))
            
            # Add a text label at the center of the cube
            fig.add_trace(go.Scatter3d(
                x=[x0 + dx/2],
                y=[y0 + dy/2],
                z=[z0 + dz/2],
                mode='text',
                text=[item['Count_ID']],
                textposition="middle center",
                textfont=dict(size=10, color="black"),
                showlegend=False
            ))
        
        # Set layout with the truck's container dimensions (14m x 2.8m x 2.8m)
        # and enforce a manual aspect ratio to maintain the rectangular shape.
        fig.update_layout(
            title=f'Truck {truckNum} Loading Visualization',
            scene=dict(
                xaxis=dict(title='Length (m)', range=[0, 14]),
                yaxis=dict(title='Width (m)', range=[0, 2.8]),
                zaxis=dict(title='Height (m)', range=[0, 2.8]),
                aspectmode='manual',
                aspectratio=dict(x=14, y=2.8, z=2.8)
            ),
            margin=dict(l=0, r=0, b=0, t=50)
        )
        
        # Display the interactive 3D figure
        fig.show()

# Usage: Replace the path below with the location of your JSON file.
visualizeTrucksPlotly("output.json")
