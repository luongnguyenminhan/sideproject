'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faGoogle } from '@fortawesome/free-brands-svg-icons';
import { Card, Button, Space, message } from 'antd';
import { useAppDispatch, useAppSelector } from '@/redux/hooks';
import { loginStart, loginSuccess, loginFailure } from '@/redux/slices/authSlice';
import authApi from '@/apis/authApi';
import Cookies from 'js-cookie';
import { getErrorMessage } from '@/utils/apiHandler';

interface LoginFormProps {
    callbackUrl?: string;
    translations: {
        login: string;
        loginWithGoogle: string;
        signInWithGoogle: string;
        bySigningIn: string;
        signingIn: string;
        loginSuccess: string;        connectingToGoogle: string;
        pleaseWait: string;
        unableToConnect: string;
        openingGoogleLogin: string;
        allowPopups: string;
    };
}

// Client Component
export default function LoginForm({ callbackUrl, translations }: LoginFormProps) {
    const [isLoading, setIsLoading] = useState(false);    const dispatch = useAppDispatch();
    const router = useRouter();
    const { isAuthenticated } = useAppSelector((state) => state.auth);

    // Handle authentication success - redirect if already authenticated
    useEffect(() => {
        if (isAuthenticated && callbackUrl) {
            router.push(callbackUrl);
        }
    }, [isAuthenticated, callbackUrl, router]);    // Listen for postMessage events from OAuth popup
    useEffect(() => {
        const handleMessage = async (event: MessageEvent) => {
            // Verify origin for security
            const apiBaseUrl =
                process.env.NEXT_PUBLIC_API_BASE_URL ||
                "http://localhost:8000/api/v1";
            const allowedOrigins = [
                new URL(apiBaseUrl).origin,
                window.location.origin,
            ];

            if (!allowedOrigins.includes(event.origin) && event.origin !== "*") {
                console.warn(
                    "Received message from unauthorized origin:",
                    event.origin
                );
                return;
            }

            // Handle authentication result
            if (
                event.data &&
                event.data.type === "GOOGLE_AUTH_SUCCESS" &&
                event.data.accessToken
            ) {
                try {
                    dispatch(loginStart());
                    setIsLoading(true);

                    Cookies.set("access_token", event.data.accessToken, { path: "/" });
                    if (event.data.refreshToken) {
                        Cookies.set("refresh_token", event.data.refreshToken, {
                            path: "/",
                        });
                    }

                    // Set the token in axios instance
                    if (authApi.setToken) {
                        authApi.setToken(event.data.accessToken);
                    }

                    // Fetch user details with the new token
                    const userDetails = await authApi.getMe();

                    if (userDetails) {
                        // Dispatch login success with user details
                        dispatch(
                            loginSuccess({
                                user: {
                                    id: userDetails.id,
                                    email: userDetails.email,
                                    username: userDetails.username,
                                    confirmed: userDetails.confirmed,
                                    role_id: userDetails.role || undefined,
                                }
                            })
                        );

                        message.success(translations.loginSuccess, 3);
                        
                        // Redirect to callback URL or home
                        setTimeout(() => {
                            router.push(callbackUrl || '/');
                        }, 1000);
                    } else {
                        throw new Error("Failed to fetch user details");
                    }
                } catch (error) {
                    console.error("Error processing Google login:", error);
                    const errorMessage =
                        error instanceof Error
                            ? error.message
                            : "Google login failed.";
                    dispatch(loginFailure(errorMessage));

                    message.error(errorMessage, 5);
                } finally {
                    setIsLoading(false);
                }
            }
            // Handle authentication error
            else if (event.data && event.data.type === "GOOGLE_AUTH_ERROR") {
                setIsLoading(false);
                const errorMessage = event.data.error || "Google login failed.";
                dispatch(loginFailure(errorMessage));

                message.error(errorMessage, 5);
            }
        };

        window.addEventListener("message", handleMessage);

        return () => {
            window.removeEventListener("message", handleMessage);
        };
    }, [dispatch, router, callbackUrl, translations]);const handleGoogleLogin = () => {
        try {
            setIsLoading(true);
            dispatch(loginStart());
            
            const apiBaseUrl =
                process.env.NEXT_PUBLIC_API_BASE_URL ||
                "http://localhost:8000/api/v1";
            const googleLoginUrl = `${apiBaseUrl}/auth/google/login`;            // Show loading message
            message.info(translations.openingGoogleLogin, 2);

            // Calculate popup window position (centered)
            const width = 600;
            const height = 700;
            const left = window.screenX + (window.outerWidth - width) / 2;
            const top = window.screenY + (window.outerHeight - height) / 2;

            // Enhanced popup window approach for better session maintenance
            // First, open a same-origin blank page to establish cookie context
            const popup = window.open(
                "about:blank",
                "GoogleLogin",
                `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes,status=yes`
            );            // Handle popup blockers
            if (!popup) {
                setIsLoading(false);
                message.error(translations.allowPopups, 5);
                return;
            }

            // Add additional metadata to the window
            if (popup.opener !== window) {
                popup.opener = window;
            }            // Show loading indicator in the popup while we navigate
            if (popup.document) {
                popup.document.write(`
                    <html>
                        <head>
                            <title>${translations.connectingToGoogle}</title>
                            <style>
                                body {
                                    font-family: Arial, sans-serif;
                                    display: flex;
                                    flex-direction: column;
                                    justify-content: center;
                                    align-items: center;
                                    height: 100vh;
                                    margin: 0;
                                    background-color: #f5f5f5;
                                    text-align: center;
                                }
                                .spinner {
                                    border: 4px solid rgba(0, 0, 0, 0.1);
                                    width: 36px;
                                    height: 36px;
                                    border-radius: 50%;
                                    border-left-color: #4285F4;
                                    animation: spin 1s linear infinite;
                                    margin: 20px auto;
                                }
                                @keyframes spin {
                                    0% { transform: rotate(0deg); }
                                    100% { transform: rotate(360deg); }
                                }
                            </style>
                        </head>
                        <body>
                            <h2>${translations.connectingToGoogle}</h2>
                            <div class="spinner"></div>
                            <p>${translations.pleaseWait}</p>
                        </body>
                    </html>
                `);
                popup.document.close();
            }

            // Delay slightly before redirecting to ensure the popup is properly initialized
            // This helps maintain session/cookie context between the main window and popup
            setTimeout(() => {
                if (popup && !popup.closed) {
                    popup.location.href = googleLoginUrl;
                } else {
                    setIsLoading(false);
                }
            }, 300);

            // Set up a checker for when the popup is closed without completing auth
            const popupChecker = setInterval(() => {
                if (!popup || popup.closed) {
                    clearInterval(popupChecker);
                    setIsLoading(false);
                }
            }, 1000);
        } catch (error) {
            console.error("Failed to initiate Google login:", error);            setIsLoading(false);
            const errorMessage = getErrorMessage(error);
            dispatch(loginFailure(errorMessage));
            message.error(translations.unableToConnect, 5);
        }
    };

    return (
        <div className="flex justify-center items-center">
            <Card 
                className="w-full max-w-md"
                style={{ boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)', borderRadius: '8px' }}
            >
                <Space direction="vertical" size="large" className="w-full">                    <div className="text-center">                          <h3 style={{ marginBottom: '8px', fontSize: '24px', fontWeight: '600' }}>
                            {translations.login}
                        </h3>
                        <p style={{ color: '#888' }}>
                            {translations.loginWithGoogle}
                        </p>
                    </div><div className="w-full">
                        <Button 
                            type="default"
                            size="large"
                            block
                            loading={isLoading}
                            onClick={handleGoogleLogin}
                            icon={<FontAwesomeIcon icon={faGoogle} style={{ color: '#4285f4' }} />}
                            style={{
                                height: '48px',
                                borderColor: '#dadce0',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '8px'
                            }}                        >                            {isLoading 
                                ? translations.signingIn 
                                : translations.signInWithGoogle
                            }
                        </Button>
                    </div>                    <div className="text-center">                        <p style={{ fontSize: '12px', color: '#888' }}>
                            {translations.bySigningIn}
                        </p>
                    </div>
                </Space>
            </Card>
        </div>
    );
}
