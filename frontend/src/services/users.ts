import { apiFetch } from "./api";

export interface UserSettings {
  email_notifications: boolean;
}

/**
 * Update user settings (CR-08)
 */
export async function updateUserSettings(settings: UserSettings): Promise<UserSettings> {
  return apiFetch<UserSettings>("/users/me/settings", {
    method: "PATCH",
    body: JSON.stringify(settings),
  });
}

/**
 * Fetch current user settings
 */
export async function fetchUserSettings(): Promise<UserSettings> {
  return apiFetch<UserSettings>("/users/me/settings");
}
