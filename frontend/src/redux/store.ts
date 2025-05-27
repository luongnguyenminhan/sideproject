import { configureStore } from '@reduxjs/toolkit'
import themeSlice from './slices/themeSlice'
import localeSlice from './slices/localeSlice'

export const store = configureStore({
  reducer: {
    theme: themeSlice,
    locale: localeSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
