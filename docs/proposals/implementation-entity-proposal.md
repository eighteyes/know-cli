# Implementation Entity Proposal

## Why Implementations Should Be Distinct Entities

### Current State
Your knowledge graph has these entities:
- **Features** - High-level capabilities (WHAT users need)
- **Components** - UI/logical parts (WHAT pieces exist)
- **Functionality** - Business capabilities (WHY it exists)

But missing:
- **Implementations** - Actual code modules (HOW it's built)

### Problems This Causes

1. **Technology Ambiguity**
   - Component says "fleet-status-map" but doesn't specify React vs Angular
   - No place to document webpack config, build process, deployment

2. **Platform Confusion**
   - Same component might have web, mobile, and desktop versions
   - Currently no way to distinguish them

3. **Dependency Gaps**
   - Components depend on features (conceptual)
   - But code depends on npm packages, APIs, services (technical)

4. **No Implementation Status**
   - Can't track: planned, in-progress, deployed, deprecated
   - Can't version: v1 (MVP), v2 (optimized), v3 (redesigned)

## Proposed Implementation Entity Structure

```json
{
  "entities": {
    "implementations": {
      "fleet-map-react-web": {
        "id": "fleet-map-react-web",
        "type": "implementation",
        "name": "Fleet Map React Web Implementation",
        "implements": "component:fleet-status-map",
        "platform": "platform:web-platform",
        "status": "deployed",
        "version": "2.3.0",
        "technology": {
          "language": "typescript",
          "framework": "react",
          "state_management": "redux-toolkit",
          "mapping_library": "mapbox-gl",
          "build_tool": "vite",
          "testing": "jest"
        },
        "dependencies": {
          "npm_packages": [
            "react@18.2.0",
            "mapbox-gl@2.15.0",
            "@reduxjs/toolkit@1.9.5"
          ],
          "apis": [
            "telemetry-websocket-api",
            "fleet-status-rest-api"
          ],
          "implementations": [
            "websocket-client-web",
            "auth-provider-web"
          ]
        },
        "repository": {
          "url": "github.com/company/fleet-ui",
          "path": "src/components/FleetMap",
          "main_file": "FleetMap.tsx"
        },
        "deployment": {
          "environment": "production",
          "url": "https://app.company.com/fleet",
          "ci_pipeline": "github-actions"
        }
      }
    }
  }
}
```

## Benefits of This Approach

### 1. Clear Separation of Concerns
```
Conceptual Layer:  User → Functionality → Feature → Component
Technical Layer:   Component → Implementation → Code/Deploy
```

### 2. Multi-Platform Support
```
component:fleet-status-map
  ├── implementation:fleet-map-react-web
  ├── implementation:fleet-map-react-native
  └── implementation:fleet-map-flutter
```

### 3. Technology Evolution
```
implementation:auth-v1-cookies (deprecated)
implementation:auth-v2-jwt (current)
implementation:auth-v3-oauth (planned)
```

### 4. Dependency Management
- **Conceptual**: Feature depends on requirements
- **Technical**: Implementation depends on npm packages
- **Operational**: Deployment depends on infrastructure

### 5. Better Spec Generation
```bash
know component fleet-status-map    # What to build
know implementation fleet-map-web  # How to build it
```

## Implementation in Your Graph

### Step 1: Add Entity Type
```bash
./know/know mod add-entity-type implementations
```

### Step 2: Create Implementations
```bash
./know/know mod add implementation:fleet-map-web \
  --implements component:fleet-status-map \
  --platform web-platform \
  --framework react
```

### Step 3: Connect Dependencies
```bash
./know/know mod connect implementation:fleet-map-web \
  uses implementation:websocket-client-web
```

### Step 4: Generate Implementation Specs
```bash
know implementation fleet-map-web  # Technical implementation spec
```

## Graph Evolution

### Before (Current)
```
users → functionality → features → components → [missing]
```

### After (Proposed)
```
users → functionality → features → components → implementations
WHO  →  WHY         →  WHAT    →  PARTS     →  HOW
```

## Migration Path

1. **Phase 1**: Add implementations for existing components
2. **Phase 2**: Link implementations to platforms
3. **Phase 3**: Document technology stacks
4. **Phase 4**: Track deployment status
5. **Phase 5**: Version management

## Use Cases Enabled

1. **Technology Audits**: "Show all React implementations"
2. **Platform Coverage**: "Which features lack mobile implementations?"
3. **Dependency Analysis**: "What breaks if we upgrade to React 19?"
4. **Resource Planning**: "What needs TypeScript migration?"
5. **Deployment Tracking**: "What's deployed vs in development?"

## Conclusion

Adding implementations as distinct entities would:
- Complete your specification hierarchy
- Enable technical documentation
- Support multi-platform development
- Track deployment lifecycle
- Bridge concept to code

This makes your knowledge graph a complete system from user needs to deployed code.