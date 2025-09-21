# Discover Page Enhancement Workflows

## Workflow 1: Session Management Backend

1. Add session tracking to `/api/discover/save-qa` endpoint
2. Create `/api/discover/session/history` endpoint
3. Create `/api/discover/session/navigate` endpoint
4. Create `/api/discover/session/progress` endpoint
5. Test all session endpoints with Postman/curl
6. Validate session persistence across server restarts

## Workflow 2: Entity Extraction Enhancement Backend

1. Modify `/api/discover/extract` to return confidence scores
2. Add entity validation before graph commit
3. Implement bulk entity extraction from single answer
4. Create entity name/description editing endpoint
5. Add entity preview before commit functionality
6. Test extraction with various answer formats

## Workflow 3: Smart Question Generation Backend

1. Enhance `/api/discover/next-question` with gap analysis
2. Add question categorization (exploration, dependency, completion)
3. Implement question chains based on entity types
4. Add skip/back navigation support
5. Create question context/guidance system
6. Test question flow logic with sample data

## Workflow 4: Q&A History Navigation Frontend

1. Create history sidebar component in `discover.js`
2. Add back/forward navigation buttons
3. Implement answered/skipped status indicators
4. Add progress indicator calculation
5. Wire up navigation to session endpoints
6. Test history navigation flow

## Workflow 5: Entity Review Modal Frontend

1. Create entity review modal component
2. Add inline editing for entity names
3. Add inline editing for entity descriptions
4. Implement accept/reject for individual entities
5. Add batch operations (accept all, reject all)
6. Wire up to entity validation endpoints

## Workflow 6: Discover UI Improvements Frontend

1. Add question context expansion panel
2. Implement multiple choice suggestions
3. Create upcoming questions preview
4. Add session save/resume capability
5. Enhance textarea with better formatting
6. Add keyboard shortcuts for navigation

## Workflow 7: Frontend Integration

1. Update `app.js` phase switching logic
2. Modify `index.html` navigation if needed
3. Add CSS for new components
4. Test phase transitions
5. Verify WebSocket updates still work
6. Test responsive design on mobile

## Workflow 8: End-to-End Testing

1. Test complete Q&A session with history
2. Verify entity extraction and editing
3. Test session persistence and resume
4. Validate question generation chains
5. Test error handling and edge cases
6. Verify integration with existing graph system