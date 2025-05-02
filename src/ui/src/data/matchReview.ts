import { RecordMatch } from "@/models/recordMatch";
import { API_URL } from "@/utils/constants";
import { deserializeRecordMatch } from "@/utils/deserializers";
import { AppError } from "@/utils/errors";

export async function getRecordMatch(id: string | null): Promise<RecordMatch> {
  const response = await fetch(`${API_URL}/demo/record/${id}`);

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
  const response = await fetch(`${API_URL}/demo/record/${id}/link`, {
    method: "POST",
  });

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
  const response = await fetch(`${API_URL}/demo/record/${id}/unlink`, {
    method: "POST",
  });

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
