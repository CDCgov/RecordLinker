import { RecordMatch } from "@/models/recordMatch";
import { deserializeRecordMatch } from "@/utils/deserializers";
import { AppError } from "@/utils/errors";
import { get, post } from "@/utils/http";

export async function getRecordMatch(id: string | null): Promise<RecordMatch> {
  const response = await get(`/demo/record/${id}`);

  if (response.ok) {
    const serializedRecordMatch = await response.json();
    return deserializeRecordMatch(serializedRecordMatch);
  } else {
    throw new AppError(
      "getRecordMatch",
      "unsuccessful HTTP response",
      response.status,
    );
  }
}

export async function linkRecordAndMatch(
  id: string | null,
): Promise<RecordMatch> {
  const response = await post(`/demo/record/${id}/link`);

  if (response.ok) {
    const serializedRecordMatch = await response.json();
    return deserializeRecordMatch(serializedRecordMatch);
  } else {
    throw new AppError(
      "linkRecordAndMatch",
      "unsuccessful HTTP response",
      response.status,
    );
  }
}

export async function unlinkRecordAndMatch(
  id: string | null,
): Promise<RecordMatch> {
  const response = await post(`/demo/record/${id}/unlink`);

  if (response.ok) {
    const serializedRecordMatch = await response.json();
    return deserializeRecordMatch(serializedRecordMatch);
  } else {
    throw new AppError(
      "unlinkRecordAndMatch",
      "unsuccessful HTTP response",
      response.status,
    );
  }
}
