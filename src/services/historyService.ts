import { getApiUrl } from './backendConfig';

export interface HistoryItem {
  timestamp: string;
  feature: string;
  details: any; // Details can be of any type depending on the feature
}

export interface UserHistoryResponse {
  history: HistoryItem[];
}

export const getUserHistory = async (): Promise<UserHistoryResponse> => {
  const response = await fetch(getApiUrl('/api/history'), {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // Important for session cookies
  });

  if (!response.ok) {
    if (response.status === 401) {
      // Handle unauthorized access, e.g., redirect to login
      console.error('Unauthorized: User not logged in or session expired.');
      // Depending on your auth flow, you might throw an error or return a specific object
      throw new Error('User unauthorized');
    }
    const errorData = await response.json().catch(() => ({ error: 'Failed to retrieve history and parse error response' }));
    throw new Error(errorData.error || `Failed to retrieve history: ${response.status}`);
  }

  return await response.json();
};
