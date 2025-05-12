import { RecordMatch } from "@/models/recordMatch";
import { deserializeRecordMatch } from "@/utils/deserializers";
import { AppError } from "@/utils/errors";
import { get, post } from "@/utils/http";

export async function getUnmatchedRecords(): Promise<RecordMatch[]> {
  const response = await get(`/demo/record?status=pending`);
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
  const response = await post(`/demo/reset`);
  if (!response.ok) {
    throw new AppError(
      "resetDemoData",
      "unsuccessful HTTP response",
      response.status,
    );
  }
  return response;
}
