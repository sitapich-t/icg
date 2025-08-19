import bpy
import bmesh

obj = bpy.context.active_object

if obj is None or obj.type != 'MESH':
    print("กรุณาเลือกวัตถุชนิด Mesh")
else:
    # กลับสู่ OBJECT mode เพื่อให้เข้าถึง mesh data ได้ถูกต้อง
    bpy.ops.object.mode_set(mode='OBJECT')
    mesh = obj.data

    # สร้าง BMesh ชั่วคราว + triangulate
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces)

    # ตรวจว่ามี UV layer ไหม
    if not bm.loops.layers.uv:
        bm.free()
        raise RuntimeError("ไม่พบ UV layer ในโมเดล — โปรดทำ UV Unwrap ก่อน (เช่น Smart UV Project)")

    uv_layer = bm.loops.layers.uv.active

    vertices = []
    uvs = []

    # เดินทุกหน้า (triangulated แล้ว จึงเป็นสามเหลี่ยม)
    for face in bm.faces:
        for loop in face.loops:
            v = loop.vert
            # world position
            world_coord = obj.matrix_world @ v.co
            vertices.extend([
                round(world_coord.x, 6),
                round(world_coord.z, 6),
                round(-world_coord.y, 6),
            ])

            # ดึง UV จาก loop
            uv = loop[uv_layer].uv
            u = float(round(uv.x, 6))
            v_ = float(round(uv.y, 6))

            # NOTE:
            # โดยทั่วไป UV จาก Blender ใช้ตรงๆได้กับ three.js
            # ถ้าพบว่า texture กลับหัว ลองสลับเป็น: v_ = 1.0 - v_
            uvs.extend([u, v_])

    bm.free()

    # แปลงเป็น JavaScript array strings
    js_vertices = ', '.join(map(str, vertices))
    js_uvs = ', '.join(map(str, uvs))

    js_output = (
        "/* Auto-exported from Blender */\n"
        "const vertices = [\n  " + js_vertices + "\n];\n\n"
        "const uvs = [\n  " + js_uvs + "\n];\n"
    )

    # เขียนลง Text Editor ชื่อ ExportedJS
    text_name = "ExportedJS"
    if text_name not in bpy.data.texts:
        bpy.data.texts.new(text_name)
    bpy.data.texts[text_name].clear()
    bpy.data.texts[text_name].write(js_output)

    print("✅ Exported vertices + UV ไปที่ TextBlock:", text_name)
