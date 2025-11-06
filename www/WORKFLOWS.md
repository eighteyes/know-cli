AI: Use TodoWrite to ensure you hit all these items. 

# Start
URL Query: ?mock=true - disables ai
## Text entry
Enter text into input, hit button, goes to Discover page, sidebar visible

## Load JSON
Load graph from selection spec-graph.json, goes to Discover page, sidebar visible

# QA 
URL : /#discover
## QA Refinement
load graph ( spec-graph.json )
ai bar : mock <enter>
type in answer input
press 'answer' - test: next question is active
answer question #2 - test: next question is active
answer question #3 - test: show modification questions section
modification / connection section showing
### Modify / Connection
test: qa section is hidden ( no input, no controls ) 
test: modification and connection interface is showing, connection should be intiially empty
add modification
test: connection list shows added modification
add connection
click commit
test: modification and connection appear in Pending Changes section
test: modification appears in sidebar
tset: validate connection is added in graph data ( Arrange Screen when ready )

## QA Expansion
on a question click 'Expand'
Test: Multiple choices are showing
click on several multiple choice options
Test: Validate those options are shown in the answer input above

## QA Reorientation
load graph ( spec-graph.json )
ai bar: type "add user tron" <enter> 
validate that the mdoification / connection screen is showing