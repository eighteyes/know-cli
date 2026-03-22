# Alternative Architectures: spec-dashboard

## Option B: Clean Architecture (~2,800 lines, 27 files)
- Full separation: server/, routes/, components/ directories
- Preact Signals for state management
- Separate route files per resource
- middleware.py for CORS/error envelope
- Better testability, more scaffolding
- **Rejected**: Over-engineered for a local single-user tool

## Option C: Pragmatic Balance (~1,470 lines, 12 files)
- aiohttp server (new dep)
- Reuses AsyncGraphManager + BaseVisualizer.extract()
- Separate component JS files
- Port theme.py to theme.js
- **Rejected**: aiohttp adds a dependency; AsyncGraphManager is overkill; separate JS files need module loading complexity without a build step
