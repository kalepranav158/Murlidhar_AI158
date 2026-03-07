/// <reference types="vite/client" />

interface ImportMetaEnv {
	readonly VITE_API_BASE_URL?: string;
	readonly VITE_GOOGLE_CLIENT_ID?: string;
}

interface GoogleCredentialResponse {
	credential?: string;
	select_by?: string;
}

interface GoogleIdConfiguration {
	client_id: string;
	callback: (response: GoogleCredentialResponse) => void;
}

interface GoogleAccountsIdApi {
	initialize: (config: GoogleIdConfiguration) => void;
	renderButton: (element: HTMLElement, options: Record<string, unknown>) => void;
}

interface Window {
	google?: {
		accounts?: {
			id?: GoogleAccountsIdApi;
		};
	};
}
