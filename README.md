# Raylib binding generator for luajit
This is a python script that generates a .lua file that binds raylib header files to a .lua file so you dont need to do it yourself.

## Issues
Since its generated with a script, it removes the macros from the headers. So some utilities like colors aren't added directly, so i created another lua file that has the colors of the raylib library.

Also it usses ffi library from luajit, so it searchs the .so files from the known standard paths. If raylib isnt installed on those paths it will fail, but you can do it with:

```
export LD_LIBRARY_PATH=/path/to/raylib/lib:$LD_LIBRARY_PATH && luajit [main file].lua

```

# Use

```
# Generate binding
python3 gen_raylib_ffi.py

# or giving the route of the header files
python3 gen_raylib_ffi.py /path/to/raylib.h -o raylib_ffi.lua

```

You can also bind raymath and rlgl.h, you just need to add the path file argument

## Example code

```lua
local ffi    = require("ffi")
local rl     = require("raylib_ffi")
local colors = require("raylib_colors")

rl.InitWindow(800, 450, "Example")

local camera = ffi.new("Camera2D")
camera.target.x = 0
camera.target.y = 0
camera.offset.x = 400
camera.offset.y = 225
camera.rotation = 0
camera.zoom = 1.0

while not rl.WindowShouldClose() do
    rl.BeginDrawing()
    rl.ClearBackground(colors.BLACK)
        rl.BeginMode2D(camera)
        rl.DrawRectangle(0,0,100,100,colors.RED)
        rl.EndMode2D()
    rl.DrawFPS(0,0)
    rl.EndDrawing()
end

rl.CloseWindow()

```
