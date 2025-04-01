import { API_URL } from "@/utils/constants";

export async function getAlgoDibbsDefault(): Promise<Record<string, string>> {
  return (await fetch(`${API_URL}/algorithm/dibbs-default`)).json();
}
