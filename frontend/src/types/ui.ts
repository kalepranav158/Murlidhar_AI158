export type AsyncState<T> = {
  loading: boolean;
  error: string | null;
  data: T | null;
};

export const initialAsyncState = <T,>(): AsyncState<T> => ({
  loading: false,
  error: null,
  data: null,
});
