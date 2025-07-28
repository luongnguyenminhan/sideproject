import { AuthState } from '@/types/common.type';
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface LoginSuccessPayload {
  user: {
    id: string;
    email: string;
    username: string;
    name?: string;
    profile_picture?: string;
    confirmed: boolean;
    role_id?: string;
    rank?: string;
    rank_activated_at?: string | Date;
    rank_expired_at?: string | Date;
  };
}

const initialState: AuthState = {
  isAuthenticated: false,
  isLoading: false,
  user: null,
  error: null,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginStart: state => {
      state.isLoading = true;
      state.error = null;
    },
    loginSuccess: (state, action: PayloadAction<LoginSuccessPayload>) => {
      state.isLoading = false;
      state.isAuthenticated = true;
      state.user = action.payload.user;
      state.error = null;
    },
    loginFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.isAuthenticated = false;
      state.user = null;
      state.error = action.payload;
    },
    logout: state => {
      state.isLoading = false;
      state.isAuthenticated = false;
      state.user = null;
      state.error = null;
    },
    clearError: state => {
      state.error = null;
    },
    setUser: (state, action: PayloadAction<LoginSuccessPayload['user']>) => {
      console.log('check action', action.payload);
      state.user = action.payload;
      state.isAuthenticated = true;
    },
  },
});

export const { loginStart, loginSuccess, loginFailure, logout, clearError, setUser } =
  authSlice.actions;
export default authSlice.reducer;
