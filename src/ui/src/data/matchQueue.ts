import { RecordMatch } from "@/models/recordMatch";
import { API_URL } from "@/utils/constants";
import { deserializeRecordMatch } from "@/utils/deserializers";
import { AppError } from "@/utils/errors";

export async function getUnmatchedRecords(): Promise<RecordMatch[]> {
  const response = await fetch(`${API_URL}/demo/record?status=pending`, {
    credentials: "include",
  });
  if (response.ok) {
    const serializedMatchList: Record<string, unknown>[] =
      await response.json();
    return serializedMatchList.map((matchItem) =>
      deserializeRecordMatch(matchItem),
    );
  } else {
    throw new AppError(
      "getUnmatchedRecords",
      "unsuccessful HTTP response",
      response.status,
    );
  }
}

export async function resetDemoData(): Promise<Response> {
  const response = await fetch(`${API_URL}/demo/reset`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
  });
  if (!response.ok) {
    throw new AppError(
      "resetDemoData",
      "unsuccessful HTTP response",
      response.status,
    );
  }
  return response;
}
