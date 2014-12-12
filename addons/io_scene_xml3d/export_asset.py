import mathutils, os, bpy, re
import base64
from xml.dom.minidom import Document, Element
from bpy_extras.io_utils import *
from .tools import Vertex, Stats

BLENDER2XML_MATERIAL = "(diffuseColor, specularColor, shininess, ambientIntensity) = xflow.blenderMaterial(diffuse_color, diffuse_intensity, specular_color, specular_intensity, specular_hardness)"

def appendUnique(mlist, value):
    if value in mlist :
        return mlist[value], False
    # Not in dict, thus add it
    index = len(mlist)
    mlist[value] = index
    return index, True

class AssetExporter:
	def __init__(self,path, scene):
		self._path = path
		self._scene = scene
		self._asset = { u"mesh": [], u"data": {}}
		self._material = {}
		self._copy_set = set()

	def add_default_material(self):
		if "defaultMaterial" in self._material:
			return

		data = []
		data.append({ "type": "float3", "name": "diffuseColor", "value": "0.8 0.8 0.8"})
		data.append({ "type": "float3", "name": "specularColor", "value": "1.0 1.0 0.1"})
		data.append({ "type": "float", "name": "ambientIntensity", "value": "0.5" })

		self._material["defaultMaterial"] = { "content": { "data": data }, "script": "urn:xml3d:shader:phong" }


	def add_material(self, material):
		materialName = material.name
		if materialName in self._material:
			return
		data = []
		data.append({ "type": "float", "name": "diffuse_intensity", "value": material.diffuse_intensity })
		data.append({ "type": "float3", "name": "diffuse_color", "value": [tuple(material.specular_color)] })
		data.append({ "type": "float", "name": "specular_intensity", "value": material.specular_intensity })
		data.append({ "type": "float3", "name": "specular_color", "value": [tuple(material.specular_color)] })
		data.append({ "type": "float", "name": "specular_hardness", "value": material.specular_hardness })
		data.append({ "type": "float", "name": "ambient", "value": material.ambient })


		for texture_index, texture_slot in enumerate(material.texture_slots) :
			if not material.use_textures[texture_index] or texture_slot == None:
				continue

			# TODO: Support uses of textures other than diffuse
			if not texture_slot.use_map_color_diffuse or texture_slot.diffuse_color_factor < 0.0001 :
				continue

			if texture_slot.texture_coords != 'UV' :
				print("Warning: Texture '%s' of material '%s' uses '%s' mapping, which is not (yet) supported. Skipping texture..."
					 % (texture_slot.name, materialName, texture_slot.texture_coords))
				continue

			texture = texture_slot.texture
			if texture.type != 'IMAGE' :
				print("Warning: Texture '%s' of material '%s' is of type '%s' which is not (yet) supported. Skipping texture..."
				% (texture_slot.name, materialName, texture.type))
				continue

			image = texture.image
			if not image.source in {'FILE', 'VIDEO'}:
				print("Warning: Texture '%s' of material '%s' is from source '%s' which is not (yet) supported. Skipping texture..."
				% (texture_slot.name, materialName, image.source))
				continue

			if image.packed_file:
				mime_type = "image/png"
				image_data = base64.b64encode(image.packed_file.data).decode("utf-8")
				image_src = "data:%s;base64,%s" % (mime_type, image_data)
			else:
				image_src = path_reference(image.filepath,
					os.path.dirname(bpy.data.filepath),
					os.path.dirname(self._path),
					'COPY',
					"../textures",
					self._copy_set,
					image.library)
				image_src = re.sub('\\\\', '/', image_src)

			# TODO: extension/clamp, filtering, sampling parameters
			# FEATURE: Resize / convert / optimize texture
			data.append({ "type": "texture", "name": "diffuseTexture", "value": image_src })

		self._material[materialName] = { "content": { "data": data }, "script": "urn:xml3d:shader:phong", "compute": BLENDER2XML_MATERIAL }



	def addMesh(self, meshObject, derivedObject):
		if derivedObject:
			for obj, mat in derivedObject:
				if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}:
					continue

				try:
					data = obj.to_mesh(self._scene, True, 'RENDER', True)
				except:
					data = None

				if data:
					self.addMeshData(data)

		else:
			print ("no derived")
			self.addMeshData(meshObject.data)



	def export_tessfaces(self, mesh):
		if not len(mesh.tessfaces):
			print("Found mesh without tessfaces: %s" % mesh.name)
			return None, None

		materialCount = len(mesh.materials)

		# Mesh indices:
		# For each material allocate an array
		indices = [[] for m in range(1 if materialCount == 0 else materialCount)] #@UnusedVariable

		# All vertices of the mesh, trying to keep the number of vertices small
		vertices = []
		# Vertex cache
		vertex_dict = {}

		uv_data = None
		if len(mesh.tessface_uv_textures):
			uv_data = [uv.data for uv in mesh.tessface_uv_textures]
			uv_data = list(zip(*uv_data))

		'''	@type bpytypes.MeshTessFace '''
		faces = mesh.tessfaces
		for faceIndex, face in enumerate(faces) :
			mv = None

			if uv_data:
				''' @type tuple(bpy.types.MeshTextureFace) '''
				uv_faces = uv_data[faceIndex]
				uv_vertices = [uv_face.uv for uv_face in uv_faces]
				uv_vertices = list(zip(*uv_vertices))

			faceIndices = []

			for i, vertexIndex in enumerate(face.vertices):
				normal = mesh.vertices[vertexIndex].normal if face.use_smooth else face.normal
				uv_vertex = uv_vertices[i][0] if uv_data else None

				mv = Vertex(vertexIndex, normal, uv_vertex)

				index, added = appendUnique(vertex_dict, mv)
				faceIndices.append(index)
				#print("enumerate: %d -> %d (%d)" % (i, vertexIndex, index))
				if added :
					vertices.append(mv)

			if len(faceIndices) == 3 :
				indices[face.material_index].extend(faceIndices)
			elif len(faceIndices) == 4 :
				face2 = [faceIndices[2], faceIndices[3], faceIndices[0]]
				faceIndices[3:] = face2
				indices[face.material_index].extend(faceIndices)
			else:
				print("Found %s vertices" % len(newFaceVertices))

		return vertices, indices


	def addMeshData(self, mesh):
		meshName = mesh.name
		#print("Writing mesh %s" % meshName)
		materialCount = len(mesh.materials)



		# Export based on tess_faces:
		vertices, indices = self.export_tessfaces(mesh)

		if not (vertices and indices):
			return
		# print("Faces: %i" % len(mesh.polygons))

		content = []
		# Vertex positions and normals
		positions = []
		normals = []
		texcoord = []
		has_texcoords = vertices[0].texcoord
		for v in vertices :
			positions.append(tuple(mesh.vertices[v.index].co))
			normals.append(tuple(v.normal))
			if has_texcoords:
				texcoord.append(tuple(v.texcoord))

		content.append({ "type": "float3", "name": "position", "value": positions})
		content.append({ "type": "float3", "name": "normal", "value": normals})
		if has_texcoords:
			content.append({ "type": "float2", "name": "texcoord", "value": texcoord})

		self._asset['data'][meshName] = { "content": content }


		for materialIndex, material in enumerate(mesh.materials if materialCount else [None]) :
			if len(indices[materialIndex]) == 0:
				continue

			materialName = material.name if material else "defaultMaterial"

			data = []
			data.append({ "type": "int", "name": "index", "value": indices[materialIndex]})

			submeshName = meshName + "_" + materialName
			self._asset['mesh'].append( {"name": submeshName, "includes": meshName, "data": data, "shader": "#"+materialName })

			if material:
				self.add_material(material)
			else:
				self.add_default_material()

	def saveXML(self, f, stats):
		doc = Document()
		xml3d = doc.createElement("xml3d")
		doc.appendChild(xml3d)

		asset = doc.createElement("asset")
		asset.setAttribute("id", "root")
		xml3d.appendChild(asset)

		for name, material in self._material.items():
			shader = doc.createElement("shader")
			shader.setAttribute("id", name)
			shader.setAttribute("script", material["script"])
			if "compute" in material:
				shader.setAttribute("compute", material["compute"])
			xml3d.appendChild(shader)
			content = material["content"]
			for entry in content["data"]:
				entryElement = AssetExporter.writeGenericContent(doc, entry, stats)
				shader.appendChild(entryElement)
			stats.materials += 1

		for name, value in self._asset["data"].items():
			assetData = doc.createElement("assetdata")
			assetData.setAttribute("name", name)
			asset.appendChild(assetData)
			for entry in value["content"]:
				entryElement = AssetExporter.writeGenericContent(doc, entry)
				assetData.appendChild(entryElement)

		for mesh in self._asset["mesh"]:
			assetMesh = doc.createElement("assetmesh")
			assetMesh.setAttribute("name", mesh["name"])
			assetMesh.setAttribute("includes", mesh["includes"])
			assetMesh.setAttribute("shader", mesh["shader"])
			asset.appendChild(assetMesh)
			for entry in mesh["data"]:
				entryElement = AssetExporter.writeGenericContent(doc, entry)
				assetMesh.appendChild(entryElement)
			stats.meshes.append(mesh["name"])

		doc.writexml(f, "", "  ", "\n", "UTF-8")

	def writeGenericContent(doc, entry, stats = None):
		entry_type = entry["type"]
		entryElement = doc.createElement(entry_type)
		entryElement.setAttribute("name", entry["name"])

		value = entry["value"]
		valueStr = None
		if (entry_type == "int"):
			valueStr = " ".join(str(e) for e in value)
		elif (entry_type == "texture"):
			imgElement = doc.createElement("img")
			imgElement.setAttribute("src", value)
			entryElement.appendChild(imgElement)
			stats.textures += 1
		else:
			if not isinstance(value, list):
				valueStr = str(value)
			else:
				valueStr = ""
				for t in value:
					length = len(t) if isinstance(t,tuple) else 1
					fs = length* "%.6f "
					valueStr += fs % t

		if valueStr:
			textNode = doc.createTextNode(valueStr)
			entryElement.appendChild(textNode)
		return entryElement

	def copy_report(self, str):
		print("Report: " + str)

	def save(self):
		stats = Stats(materials = 0, meshes = [], assets=[], textures = 0)
		stats.assets.append({ "url": self._path })

		with open (self._path, "w") as assetFile:
			self.saveXML(assetFile, stats)
			assetFile.close()
			os.path.getsize(self._path)
			stats.assets[0]["size"] = os.path.getsize(self._path)

		try:
			path_reference_copy(self._copy_set, self.copy_report)
		except PermissionError:
			print('ERROR: While copying textures: %s' % self._copy_set)

		return stats
