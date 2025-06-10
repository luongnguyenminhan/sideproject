'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faGoogle } from '@fortawesome/free-brands-svg-icons';
import { faTimes } from '@fortawesome/free-solid-svg-icons';
import { Modal, Button, Space, message } from 'antd';
import { useAppDispatch, useAppSelector } from '@/redux/hooks';
import { loginStart, loginSuccess, loginFailure } from '@/redux/slices/authSlice';
import authApi from '@/apis/authApi';
import Cookies from 'js-cookie';
import { getErrorMessage } from '@/utils/apiHandler';
import React from 'react';

interface LoginModalProps {
    isOpen: boolean;
    onClose: () => void;
    callbackUrl?: string;
    onSuccess?: () => void;
    t: (key: string) => string; // Replace translations object with t function
}

export default function LoginModal({ isOpen, onClose, callbackUrl, onSuccess, t }: LoginModalProps) {
    const [isLoading, setIsLoading] = useState(false);
    const dispatch = useAppDispatch();
    const router = useRouter();
    const { isAuthenticated } = useAppSelector((state) => state.auth);

    // Handle authentication success - close modal and redirect if needed
    useEffect(() => {
        if (isAuthenticated && isOpen) {
            onClose();
            if (callbackUrl) {
                router.push(callbackUrl);
            }
        }
    }, [isAuthenticated, isOpen, callbackUrl, router, onClose]);

    // Listen for postMessage events from OAuth popup
    useEffect(() => {
        const handleMessage = async (event: MessageEvent) => {
            // Verify origin for security
            const apiBaseUrl =
                process.env.NEXT_PUBLIC_API_BASE_URL ||
                "https://api.wc504.io.vn/api/v1";
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

                        message.success(t('auth.loginSuccess'), 3);
                        
                        // Call success callback if provided
                        if (onSuccess) {
                            onSuccess();
                        }
                        
                        // Close modal and redirect
                        setTimeout(() => {
                            onClose();
                            if (callbackUrl) {
                                router.push(callbackUrl);
                            }
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
    }, [dispatch, router, callbackUrl, t, onClose, onSuccess]);

    const handleGoogleLogin = () => {
        try {
            setIsLoading(true);
            dispatch(loginStart());
            
            const apiBaseUrl =
                process.env.NEXT_PUBLIC_API_BASE_URL ||
                "https://api.wc504.io.vn/api/v1";
            const googleLoginUrl = `${apiBaseUrl}/auth/google/login`;

            // Show loading message
            message.info(t('auth.openingGoogleLogin'), 2);

            // Calculate popup window position (centered)
            const width = 600;
            const height = 700;
            const left = window.screenX + (window.outerWidth - width) / 2;
            const top = window.screenY + (window.outerHeight - height) / 2;

            // Enhanced popup window approach for better session maintenance
            const popup = window.open(
                "about:blank",
                "GoogleLogin",
                `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes,status=yes`
            );

            // Handle popup blockers
            if (!popup) {
                setIsLoading(false);
                message.error(t('auth.allowPopups'), 5);
                return;
            }

            // Add additional metadata to the window
            if (popup.opener !== window) {
                popup.opener = window;
            }

            // Show loading indicator in the popup while we navigate
            if (popup.document) {
                popup.document.write(`
                    <html>
                        <head>
                            <title>${t('auth.connectingToGoogle')}</title>
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
                            <h2>${t('auth.connectingToGoogle')}</h2>
                            <div class="spinner"></div>
                            <p>${t('auth.pleaseWait')}</p>
                        </body>
                    </html>
                `);
                popup.document.close();
            }

            // Delay slightly before redirecting to ensure the popup is properly initialized
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
            console.error("Failed to initiate Google login:", error);
            setIsLoading(false);
            const errorMessage = getErrorMessage(error);
            dispatch(loginFailure(errorMessage));
            message.error(t('auth.unableToConnect'), 5);
        }
    };

    return (
        <Modal
            open={isOpen}
            onCancel={onClose}
            footer={null}
            centered
            width={480}
            closeIcon={
                <FontAwesomeIcon 
                    icon={faTimes} 
                    className="text-gray-500 hover:text-gray-700 text-lg" 
                />
            }
            styles={{
                content: {
                    borderRadius: '20px',
                    padding: 0,
                    background: 'var(--auth-card-bg)',
                    border: '1px solid var(--auth-card-border)'
                },
                mask: {
                    backdropFilter: 'blur(8px)',
                    backgroundColor: 'rgba(0, 0, 0, 0.5)'
                }
            }}
        >
            <div className="p-8">
                <Space direction="vertical" size="large" className="w-full">
                    <div className="text-center space-y-4">
                        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[color:var(--gradient-text-from)] via-[color:var(--gradient-text-via)] to-[color:var(--gradient-text-to)]">
                            {t('auth.login')}
                        </h1>
                        <p className="text-gray-600 dark:text-gray-300 text-lg font-medium">
                            {t('auth.loginWithGoogle')}
                        </p>
                    </div>

                    <div className="w-full mt-8">
                        <Button 
                            type="default"
                            size="large"
                            block
                            loading={isLoading}
                            onClick={handleGoogleLogin}
                            className="transition-all duration-200 hover:shadow-lg"
                            style={{
                                height: '56px',
                                borderRadius: '16px',
                                border: 'none',
                                background: isLoading 
                                    ? '#e5e7eb'
                                    : '#ffffff',
                                boxShadow: '0 4px 15px rgba(0, 0, 0, 0.1)',
                                color: '#374151',
                                fontWeight: '600',
                                fontSize: '16px'
                            }}
                        >
                            <div className="flex items-center justify-center gap-3">
                                {isLoading ? (
                                    <>
                                        <div className="w-5 h-5 border-2 border-gray-400 border-t-blue-500 rounded-full animate-spin"></div>
                                        <span>{t('auth.signingIn')}</span>
                                    </>
                                ) : (
                                    <>
                                        <FontAwesomeIcon 
                                            icon={faGoogle} 
                                            className="text-[#4285f4]" 
                                            size="lg"
                                        />
                                        <span>{t('auth.signInWithGoogle')}</span>
                                    </>
                                )}
                            </div>
                        </Button>
                    </div>

                    <div className="text-center mt-6 pt-4 border-t border-gray-100 dark:border-gray-700">
                        <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed">
                            {t('auth.bySigningIn')}
                        </p>
                    </div>
                </Space>
            </div>
        </Modal>
    );
}
