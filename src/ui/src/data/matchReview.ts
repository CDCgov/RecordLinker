import { RecordMatch } from "@/models/recordMatch";
import { API_URL } from "@/utils/constants";
import { deserializeToRecordMatch } from "@/utils/deserializers";

export async function getRecordMatch(id: string | null): Promise<RecordMatch> {
  const response = await fetch(`${API_URL}/demo/record/${id}`);

  if (response.ok) {
    return response
      .json()
      .then((response) => deserializeToRecordMatch(response));
  } else {
    throw new Error(response.status.toString());
  }
}
