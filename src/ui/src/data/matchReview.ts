import { RecordMatch } from "@/models/recordMatch";
import { API_URL } from "@/utils/constants";
import { deserializeRecordMatch } from "@/utils/deserializers";
import { AppError } from "@/utils/errors";

export async function getRecordMatch(id: string | null): Promise<RecordMatch> {
  const response = await fetch(`${API_URL}/demo/record/${id}`, {
    credentials: "include",
  });

  if (response.ok) {
    const serializedRecordMatch = await response.json();
    return deserializeRecordMatch(serializedRecordMatch);
  } else {
    throw new AppError(
      "getRecordMatch",
      "unsuccessful HTTP response",
      response.status
    );
  }
}
