export interface User {
    id: string;
    full_name: string;
    username: string;
    email: string;
    mobile: string;
    age: number;
    gender: string;
    address?: string;
}

export interface RegisterData {
    full_name: string;
    username: string;
    email: string;
    mobile: string;
    age: number;
    gender: string;
    address?: string;
    password: string;
}

export interface LoginData {
    username: string;
    password: string;
}

export interface Upload {
    upload_id: string;
    user_id: string;
    filename: string;
    description?: string;
    file_path: string;
    vector_status: string;
    vector_id?: string;
    extracted_content?: string;
    additional_notes?: string;
    created_at: string;
    updated_at: string;
}

export interface ChatMessage {
    role: 'user' | 'agent';
    content: string;
    agent?: string;
    timestamp: Date;
}

export interface ChatResponse {
    agent: string;
    response: string;
    vector_id: string;
}
