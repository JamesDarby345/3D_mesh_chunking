# 3D_mesh_chunking

## Purpose of this repo:
On a [request](https://discord.com/channels/1079907749569237093/1225202082147991722/1250500638425616421) by the segmentation team to provide .obj files chunked into 3d cubes to see if khartes could help specify the faces faster. It also partially addresses this bullet point in the requested open source ideas:

Mesh chunker: tool to translate a set of input meshes into a set of annotated cubes of configurable size. Each cube should represent/store each intersecting papyrus segment as its own mesh (continuous, manifold, non-intersecting)

The script can be used on any collection of .obj files with configurable cube sizes, but has already been run on the gp region in scroll 1 with 256 cubed sizes and the results uploaded to https://dl.ash2txt.org/community-uploads/james/chunked_objs/ . The origianl code was very slow, cumbersome, and complicated but this refactored &updated version runs in a reasonable amount of time and is parralelized.

## Install Instructions:
```
conda create --name 3D_mesh_chunking
conda activate 3D_mesh_chunking
conda install -c conda-forge numpy trimesh scipy
```
Note that pip wasnt working for trimesh so I installed the dependencies with conda


## Resulting cube of chunked .obj files visualised in khartes:
<img width="681" alt="Screenshot 2024-04-06 at 6 00 36 PM" src="https://github.com/JamesDarby345/3D_mesh_chunking/assets/49734270/24fb1aab-eeb1-41b5-9f47-28d3098d2cc8">
