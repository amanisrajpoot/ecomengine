import { createApiClient } from "@commerce/api-client";

import { session } from "./session";

export function getApiClient() {
  return createApiClient({
    getAccessToken: () => session.getAccessToken(),
    getTenantId: () => session.getTenantId(),
  });
}
