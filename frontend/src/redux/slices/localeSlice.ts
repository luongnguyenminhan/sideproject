import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { type Locale } from '@/i18n.config'

interface LocaleState {
  currentLocale: Locale
  isLoading: boolean
}

const initialState: LocaleState = {
  currentLocale: 'vi',
  isLoading: false,
}

export const localeSlice = createSlice({
  name: 'locale',
  initialState,
  reducers: {
    setLocale: (state, action: PayloadAction<Locale>) => {
      state.currentLocale = action.payload
    },
    setLocaleLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
  },
})

export const { setLocale, setLocaleLoading } = localeSlice.actions

export default localeSlice.reducer 