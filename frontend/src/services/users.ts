import { apiFetch } from "./api";

export interface UserSettings {
  email_notifications: boolean;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  settings: UserSettings;
}

export async function fetchUserProfile(): Promise<UserProfile> {
  return apiFetch<UserProfile>("/users/me");
}

export async function updateUserSettings(settings: UserSettings): Promise<UserProfile> {
  return apiFetch<UserProfile>("/users/me/settings", {
    method: "PATCH",
    body: JSON.stringify(settings),
  });
}
