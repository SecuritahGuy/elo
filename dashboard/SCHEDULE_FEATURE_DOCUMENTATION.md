# NFL Schedule View Feature

## Overview
The NFL Schedule View provides a comprehensive week-by-week display of NFL games with integrated ELO ratings for team comparison. This feature allows users to navigate through different weeks of the season and compare team strengths using ELO ratings.

## Features

### 🗓️ Week-by-Week Navigation
- **Week Selector**: Dropdown to select any week (1-18) of the regular season
- **Navigation Arrows**: Previous/Next week buttons for easy navigation
- **Current Week Display**: Clear indication of the currently selected week

### 📊 ELO Integration
- **Team ELO Ratings**: Display current ELO rating for each team
- **ELO Changes**: Show recent rating changes with visual indicators
- **Team Records**: Display win-loss records alongside ELO ratings
- **ELO Favorites**: Highlight the team with higher ELO rating
- **ELO Difference**: Show the point difference between teams

### 🎮 Interactive Elements
- **Refresh Button**: Manual refresh of schedule data
- **Responsive Design**: Works on desktop and mobile devices
- **Loading States**: Smooth loading indicators during data fetch

### 📱 Game Information
- **Game Times**: Local time display with timezone information
- **Venue Details**: Stadium names and locations
- **Game Status**: Live, scheduled, or completed status indicators
- **Team Matchups**: Clear home vs away team display

## Technical Implementation

### Frontend Components
- **NFLSchedule.js**: Main schedule component
- **API Integration**: Uses `apiService.getNFLSchedule()` for data fetching
- **ELO Data**: Integrates with existing ELO rating system

### Backend API
- **Endpoint**: `/api/sports/nfl/schedule`
- **Parameters**: 
  - `week`: Optional week number (1-18)
  - `season`: Season year (default: 2025)
- **Response**: Games with team details, ELO data, and venue information

### Database Schema
The schedule feature leverages the existing unified database structure:
- **games**: Core game information
- **teams**: Team details and abbreviations
- **venues**: Stadium and location data
- **seasons**: Season and week information

## Usage

### Accessing the Schedule
1. Navigate to the NFL Dashboard
2. Click on "Schedule" in the navigation menu
3. Use the week selector or navigation arrows to browse different weeks

### Understanding ELO Display
- **Green Arrow Up**: Recent ELO increase
- **Red Arrow Down**: Recent ELO decrease
- **Blue Border**: Team with higher ELO (favorite)
- **Rating Numbers**: Current ELO rating (e.g., 1650.5)
- **Change Numbers**: Recent change (e.g., +12.3, -8.7)

### Game Information
- **Team Names**: Full team names with abbreviations
- **Records**: Win-loss records (e.g., 12-5)
- **Times**: Local game times with timezone
- **Venues**: Stadium names and locations

## API Endpoints

### GET /api/sports/nfl/schedule
Retrieve NFL schedule data with optional week filtering.

**Query Parameters:**
- `week` (optional): Week number (1-18)
- `season` (optional): Season year (default: 2025)

**Response Format:**
```json
{
  "sport": "nfl",
  "season": 2025,
  "week": 1,
  "games": [
    {
      "id": 1,
      "week": 1,
      "date": "2025-01-05",
      "time_local": "13:00:00",
      "status": "scheduled",
      "home_team": {
        "id": 1,
        "name": "Philadelphia Eagles",
        "abbreviation": "PHI"
      },
      "away_team": {
        "id": 2,
        "name": "Dallas Cowboys",
        "abbreviation": "DAL"
      },
      "venue": {
        "name": "Lincoln Financial Field",
        "city": "Philadelphia",
        "state": "PA"
      }
    }
  ],
  "total_games": 1
}
```

## Testing

The schedule feature includes comprehensive test coverage:
- **Component Tests**: Loading states, navigation, data display
- **API Integration**: Mock API responses and error handling
- **User Interactions**: Week selection, refresh functionality
- **ELO Integration**: Rating display and comparison logic

## Future Enhancements

### Planned Features
- **Live Game Updates**: Real-time score updates during games
- **Playoff Schedule**: Extended schedule for playoff weeks
- **Team Filtering**: Filter games by specific teams
- **Export Options**: Download schedule data
- **Mobile Optimization**: Enhanced mobile experience

### Potential Improvements
- **Weather Integration**: Weather conditions for outdoor games
- **Injury Reports**: Key player injury information
- **Betting Lines**: Integration with betting odds
- **Social Features**: Share games and predictions

## Dependencies

### Frontend
- React 18+
- Lucide React (icons)
- Tailwind CSS (styling)
- Axios (API calls)

### Backend
- Flask (API server)
- SQLite (database)
- Python 3.8+

## Configuration

### Environment Variables
- `REACT_APP_API_BASE_URL`: API server URL
- `REACT_APP_DEFAULT_SEASON`: Default season year

### Database Setup
Ensure the unified database contains:
- NFL teams with proper abbreviations
- Game data with week numbers
- Venue information
- ELO rating data

## Troubleshooting

### Common Issues
1. **No Games Displayed**: Check if games exist for selected week
2. **ELO Data Missing**: Verify ELO ratings are loaded
3. **API Errors**: Check API server status and database connection
4. **Week Navigation**: Ensure week numbers are valid (1-18)

### Debug Steps
1. Check browser console for errors
2. Verify API endpoints are responding
3. Confirm database contains required data
4. Test with different weeks and seasons
