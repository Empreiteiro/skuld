# Buffer Development Rules

## Frontend Rules

### Component Structure
1. Each component must have its own CSS file
2. Components must be functional (not classes)
3. Use hooks for state management
4. Keep components small and focused on a single responsibility

### Styling
1. Use modular CSS per component
2. Follow the color pattern:
   - Primary: #007bff (blue)
   - Success: #28a745 (green)
   - Error: #dc3545 (red)
   - Dark background: #1a1a1a
   - Light background: #f5f5f5
3. Maintain consistent spacing:
   - Default padding: 20px
   - Element margins: 8px, 16px, 24px
4. Use flexbox for layouts

### Forms
1. Always include required field validation
2. Provide visual feedback for errors
3. Use informative placeholders
4. Maintain consistent input styling

### API Integration
1. Use fetch for API calls
2. Handle errors appropriately
3. Show user feedback during operations
4. Use relative URLs for endpoints

## Backend Rules

### API Endpoints
1. Follow REST pattern
2. Use appropriate HTTP verbs
3. Return correct HTTP codes
4. Include descriptive error messages

### Database
1. Use SQLite for development
2. Keep migrations organized
3. Validate data before saving
4. Use transactions when necessary

### Security
1. Validate all inputs
2. Sanitize data before saving
3. Use prepared statements
4. Implement rate limiting

### Logging
1. Log all executions
2. Include UTC timestamps
3. Keep logs for 30 days
4. Log errors with details

## General

### Versioning
1. Use Git Flow
2. Descriptive commits
3. feature/ branches for new features
4. hotfix/ branches for urgent fixes

### Documentation
1. Keep README updated
2. Document APIs
3. Include comments for complex code
4. Document architectural decisions

### Performance
1. Optimize queries
2. Implement caching when needed
3. Minimize API calls
4. Lazy load components

### Testing
1. Unit tests for complex logic
2. Integration tests for APIs
3. UI tests for critical components
4. Maintain test coverage > 80%

### Accessibility
1. Use semantic HTML
2. Include ARIA attributes
3. Maintain adequate contrast
4. Support keyboard navigation

### Internationalization
1. Use user's timezone
2. Format dates locally
3. Prepare for multiple languages
4. Use consistent date/time formats

### Responsiveness
1. Mobile-first design
2. Consistent breakpoints
3. Test on multiple devices
4. Keep UI functional at all resolutions 