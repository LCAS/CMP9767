# Dev Container Image Build System Usage Guide

This repository (LCAS/CMP9767) serves as the **image builder repository** for creating standardized development container images used by students in robotics courses. It implements an automated build pipeline that creates ready-to-use development environments containing all necessary ROS2 packages, dependencies, and tools.

## Repository Structure Overview

```
├── src/                          # Source packages to be included in the container
│   └── cmp9767_tutorial/         # Course-specific ROS2 packages
├── .devcontainer/                # Container build configuration
│   ├── devcontainer.json         # Dev container settings for this repo
│   ├── Dockerfile                # Multi-stage build instructions
│   └── post-create.sh            # Container initialization script
├── .github/workflows/            # Automated build pipelines
│   ├── container-build.yml       # Main image build workflow
│   └── dev-container.yml         # CI validation workflow  
├── config/                       # Configuration files
├── maps/                         # Map files for navigation
├── params/                       # Parameter files
└── worlds/                       # Simulation world files
```

## How It Works

### 1. Package Development Phase

**Add packages to the `src/` directory:**
- **Your own packages**: Create ROS2 packages directly in `src/` with proper `package.xml` files (e.g. using `ros2 pkg create`)
- **External packages**: Add as git submodules to integrate other repositories
- **Dependencies**: List all ROS dependencies in `package.xml` files - they will be automatically installed

**Example structure:**
```
src/
├── cmp9767_tutorial/             # Main course package
│   ├── package.xml               # Dependencies declared here
│   ├── setup.py                  # Python package setup
│   └── cmp9767_tutorial/         # Python modules
└── external_package/             # Git submodule (optional)
    └── package.xml
```

### 2. Automated Build Process

The build system uses a **multi-stage Dockerfile** approach:

#### Stage 1: Source Analysis (`sourcefilter`)
```dockerfile
# Copies only package.xml files to analyze dependencies
COPY ./src/*/package.xml /tmp/src/_workspace/src/_pkgs_xmls
COPY ./src/*/*/package.xml /tmp/src/_workspace/src/_pkgs_xmls
# ... (handles nested package structures)
```

#### Stage 2: Dependency Installation (`devcontainer`)
```dockerfile
# Installs all ROS dependencies using rosdep
RUN rosdep install --from-paths /tmp/src --ignore-src -y
```

#### Stage 3: Package Compilation (`compiled`)
```dockerfile
# Copies full source code and builds all packages
COPY ./src /opt/ros/lcas/src/workspace/src
RUN cd /opt/ros/lcas && colcon build
```

### 3. Automated Publishing

The **container-build.yml** workflow:
- Triggers on pushes to `main` branch and version tags
- Builds multi-architecture images (AMD64, ARM64)
- Publishes to `lcas.lincoln.ac.uk/lcas/cmp9767`
- Uses layer caching for faster builds

Key workflow features:
```yaml
platforms: linux/amd64,linux/arm64
push: true
cache-from: type=registry,ref=lcas.lincoln.ac.uk/cache/lcas/cmp9767:latest
tags: |
  type=raw,value=staging
  type=ref,event=branch
  type=semver,pattern={{version}}
```

## Student Template Repository Pattern

### Creating Student Repositories

Students are recommended to use a **separate template repository** (e.g. like [cmp3103-ws](https://github.com/UoL-SoCS/cmp3103-ws)) that:

1. **Does NOT contain a Dockerfile** (no local building)
2. **References the pre-built image** from this repository
3. **Provides a clean workspace** for student development

### Student Repository Structure
```
student-workspace/
├── .devcontainer/
│   ├── devcontainer.json         # Points to pre-built image (very much similar to this repo's devcontainer.json, but with `image` instead of `build)
│   └── post-create.sh            # Student-specific setup (usually copy from the post-create.sh above)
├── src/                          # Student's ROS2 packages
└── README.md                     # Development instructions
```

### Student devcontainer.json Configuration
```json
{
  "name": "Student Development Environment",
  "image": "lcas.lincoln.ac.uk/lcas/cmp9767:latest",
  "forwardPorts": [5801],
  "portsAttributes": {
    "5801": {
      "label": "desktop",
      "onAutoForward": "openBrowser"
    }
  },
  "postStartCommand": "/opt/entrypoint.sh /bin/true; .devcontainer/post-create.sh",
  "remoteUser": "ros",
  "updateRemoteUserUID": true,
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-vscode.cpptools",
        "JaehyunShim.vscode-ros2",
        "nonanonno.vscode-ros2",
        "deitry.colcon-helper"
      ]
    }
  }
}
```

## Development Workflow

### For Course Maintainers (This Repository)

1. **Add/Update Packages**:
   ```bash
   # Add your package to src/
   cd src/
   ros2 pkg create my_new_package --build-type ament_python
   
   # Or add external package as submodule
   git submodule add https://github.com/user/ros2-package.git src/external_package
   ```

2. **Update Dependencies**:
   - Edit `package.xml` files to declare all ROS dependencies
   - The build system automatically installs them via `rosdep`

3. **Test Locally**:
   ```bash
   # Build and test in this repository's devcontainer
   colcon build --symlink-install
   ```

4. **Publish**:
   - Push to `main` branch → triggers automatic build
   - Create version tag → creates versioned image
   ```bash
   git tag v1.2.3
   git push origin v1.2.3
   ```

### For Students (Template Repository)

1. **Create Repository**: Use template repository to create private workspace
2. **Clone and Open**: Clone in VS Code and "Reopen in Container"
3. **Develop**: Add packages to `src/`, build with `colcon build`
4. **Access Tools**: Use virtual desktop (port 5801) for GUI applications

## Image Registry and Versioning

### Available Images
- **Latest**: `lcas.lincoln.ac.uk/lcas/cmp9767:latest`
- **Versioned**: `lcas.lincoln.ac.uk/lcas/cmp9767:1.0.0`
- **Branch**: `lcas.lincoln.ac.uk/lcas/cmp9767:main`

### Recommended Student Configuration
```json
{
  "image": "lcas.lincoln.ac.uk/lcas/cmp9767:latest"
}
```

## Key Features

### Automatic Dependency Management
- **No manual Dockerfile editing** required for new ROS packages
- **rosdep integration** installs all declared dependencies
- **Multi-level package detection** supports nested package structures

### Performance Optimizations
- **Multi-stage builds** minimize final image size
- **Layer caching** speeds up subsequent builds
- **Dependency pre-installation** reduces student setup time

### Development Environment
- **Virtual desktop** with 3D acceleration support
- **Pre-configured VS Code extensions** for ROS2 development
- **Automatic workspace building** on container startup
- **Port forwarding** for web-based interfaces

## Troubleshooting

### Common Issues

1. **Build failures**: Check `package.xml` dependencies are correctly declared
2. **Missing packages**: Ensure packages are properly placed in `src/` with `package.xml`
3. **Permission issues**: Verify `updateRemoteUserUID: true` in student devcontainer.json

### Debugging Builds
- Check GitHub Actions logs in the repository
- Test locally using this repository's devcontainer
- Verify rosdep can resolve all dependencies

## Best Practices

1. **Keep this repository clean**: Only include essential course packages
2. **Use semantic versioning**: Tag releases for stable environments
3. **Test before publishing**: Use staging builds for validation
4. **Document changes**: Update this file when adding new packages
5. **Minimize dependencies**: Only add what students actually need

## Migration Guide

To migrate from local Dockerfile builds to this system:

1. **Move packages**: Copy ROS2 packages to this repository's `src/`
2. **Update student repos**: Replace Dockerfile with image reference
3. **Version control**: Tag this repository for stable releases
4. **Update documentation**: Point students to new template repository

This system provides a scalable, maintainable approach to managing development environments for robotics education, separating the complexity of image building from student development workflows.