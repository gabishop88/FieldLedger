export const authKeys = {
  all: ["auth"] as const,
  currentUser: () => [...authKeys.all, "currentUser"] as const,
} as const;

export const jdKeys = {
  all: ["jd"] as const,
  auth: () => [...jdKeys.all, "auth"] as const,
  syncTree: () => [...jdKeys.all, "syncTree"] as const,
  prepOp: (uri?: string) => [...jdKeys.all, "prepOp", uri] as const,
} as const;
