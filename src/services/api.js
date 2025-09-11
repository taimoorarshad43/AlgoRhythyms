// API service for fetching names from backend
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  async fetchNames() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/names`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.names || [];
    } catch (error) {
      console.error('Error fetching names:', error);
      // Return mock data for development
      return this.getMockNames();
    }
  }

  getMockNames() {
    return [
      'Alice Johnson',
      'Bob Smith',
      'Carol Davis',
      'David Wilson',
      'Emma Brown',
      'Frank Miller',
      'Grace Lee',
      'Henry Taylor',
      'Ivy Chen',
      'Jack Anderson',
      'Kate Martinez',
      'Liam Thompson',
      'Maya Rodriguez',
      'Noah Garcia',
      'Olivia White',
      'Paul Harris',
      'Quinn Clark',
      'Ruby Lewis',
      'Sam Walker',
      'Tina Hall'
    ];
  }

  async addName(name) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/names`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error adding name:', error);
      throw error;
    }
  }

  async removeName(name) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/names`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error removing name:', error);
      throw error;
    }
  }
}

export default new ApiService();
