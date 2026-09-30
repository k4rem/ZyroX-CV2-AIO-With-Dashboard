/** Serializable data handed from the server layout to the client shell. */
export interface ShellGuild {
  id: string;
  name: string;
  iconUrl: string | null;
}

export interface ShellUser {
  id: string;
  name: string | null;
  image: string | null;
}
