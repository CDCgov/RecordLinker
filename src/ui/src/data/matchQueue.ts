import { RecordMatch } from "@/models/recordMatch";
import { API_URL } from "@/utils/constants";
import { deserializeToRecordMatch } from "@/utils/deserializers";

export async function getUnmatchedRecords(): Promise<RecordMatch[]> {
  const response = await fetch(`${API_URL}/demo/record?status=pending`);

  if (response.ok) {
    return response.json().then((response: Record<string, unknown>[]) => {
      return response.map((matchItem) => deserializeToRecordMatch(matchItem));
    });
  } else {
    throw new Error(response.status.toString());
  }
}
