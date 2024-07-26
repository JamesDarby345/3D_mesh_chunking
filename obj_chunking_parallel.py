import os
import trimesh
import numpy as np
import concurrent.futures

# Check if PIL is installed
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("WARNING: PIL is not installed. Texture information will not be preserved.")
    print("To install PIL, run: pip install Pillow")

def get_file_names(directory):
    file_names = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".obj"):
                file_names.append(file)
    return file_names

def partition_mesh(mesh, chunk_size, padding=0, z_start=None, z_end=None, y_start=None, y_end=None, x_start=None, x_end=None):
    vertices = mesh.vertices
    
    z_min = z_start if z_start is not None else int(np.floor(vertices[:, 2].min() / chunk_size) * chunk_size)
    z_max = z_end if z_end is not None else int(np.ceil(vertices[:, 2].max() / chunk_size) * chunk_size)
    y_min = y_start if y_start is not None else int(np.floor(vertices[:, 1].min() / chunk_size) * chunk_size)
    y_max = y_end if y_end is not None else int(np.ceil(vertices[:, 1].max() / chunk_size) * chunk_size)
    x_min = x_start if x_start is not None else int(np.floor(vertices[:, 0].min() / chunk_size) * chunk_size)
    x_max = x_end if x_end is not None else int(np.ceil(vertices[:, 0].max() / chunk_size) * chunk_size)
    
    print("Ranges, z:", z_min, z_max, "y:", y_min, y_max, "x:", x_min, x_max)

    z_range = np.arange(z_min, z_max + chunk_size, chunk_size)
    y_range = np.arange(y_min, y_max + chunk_size, chunk_size)
    x_range = np.arange(x_min, x_max + chunk_size, chunk_size)

    chunks = {}
    
    for z in z_range:
        for y in y_range:
            for x in x_range:
                min_bound = np.array([x, y, z]) - padding
                max_bound = min_bound + chunk_size + 2*padding
                
                indices = np.where(
                    (vertices[:, 0] >= min_bound[0]) & (vertices[:, 0] < max_bound[0]) &
                    (vertices[:, 1] >= min_bound[1]) & (vertices[:, 1] < max_bound[1]) &
                    (vertices[:, 2] >= min_bound[2]) & (vertices[:, 2] < max_bound[2])
                )[0]
                
                if len(indices) > 0:
                    chunk_key = (z, y, x)
                    chunks[chunk_key] = indices

    return chunks

def save_mesh_chunks(mesh, chunks, current_directory, chunk_size, padding, i):
    for chunk_key, indices in chunks.items():
        filtered_vertices = mesh.vertices[indices]
        
        vertex_map = {old_idx: new_idx for new_idx, old_idx in enumerate(indices)}

        filtered_faces = []
        for face in mesh.faces:
            if all(vertex in vertex_map for vertex in face):
                filtered_faces.append([vertex_map[vertex] for vertex in face])

        if filtered_faces:
            chunk_mesh = trimesh.Trimesh(vertices=filtered_vertices, faces=np.array(filtered_faces))
            
            if PIL_AVAILABLE and mesh.visual.kind == 'texture' and mesh.visual.uv is not None:
                chunk_mesh.visual = trimesh.visual.TextureVisuals(uv=mesh.visual.uv[indices])
            
            output_dir = f"{current_directory}/output/chunked_meshes_pad{padding}_chunk_size{chunk_size}/Scroll1/{chunk_key[0]}_{chunk_key[1]}_{chunk_key[2]}_zyx"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            chunk_mesh.export(output_dir + f"/{chunk_key[0]}_{chunk_key[1]}_{chunk_key[2]}_zyx_mesh_{i}.obj")

def process_mesh(mesh, current_directory, chunk_size, i, padding=0, z_start=None, z_end=None, y_start=None, y_end=None, x_start=None, x_end=None):
    chunks = partition_mesh(mesh, chunk_size, padding=padding, z_start=z_start, z_end=z_end, y_start=y_start, y_end=y_end, x_start=x_start, x_end=x_end)
    save_mesh_chunks(mesh, chunks, current_directory, chunk_size, padding, i)

def main(meshes, current_directory, chunk_size, padding, z_start=None, z_end=None, y_start=None, y_end=None, x_start=None, x_end=None):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(process_mesh, meshes[i], current_directory, chunk_size, i, padding=padding, 
                                   z_start=z_start, z_end=z_end, y_start=y_start, y_end=y_end, x_start=x_start, x_end=x_end) 
                   for i in range(len(meshes))]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Task generated an exception: {e}")

if __name__ == "__main__":
    obj_path = "/Volumes/16TB_RAID_0/Scroll1/segments/objs"  # Change path to folder with obj files
    obj_files = get_file_names(obj_path)
    print(obj_files)
    meshes = []
    for obj in obj_files:
        meshes.append(trimesh.load_mesh(f"{obj_path}/{obj}"))
    print("meshes loaded")
    current_directory = os.getcwd()
    chunk_size = 256  # Replace with chunk size in units
    padding = 50  # Replace with padding in units

    # Specify the range of z,y,x values to chunk
    z_start = None  # Start chunking from this z value
    z_end = None  # Set to None to chunk until the end of the mesh in z direction
    y_start = None  # Set to None to start from the beginning of the mesh in y direction
    y_end = None  # Set to None to chunk until the end of the mesh in y direction
    x_start = None  # Set to None to start from the beginning of the mesh in x direction
    x_end = None  # Set to None to chunk until the end of the mesh in x direction

    main(meshes, current_directory, chunk_size, padding, z_start=z_start, z_end=z_end, y_start=y_start, y_end=y_end, x_start=x_start, x_end=x_end)