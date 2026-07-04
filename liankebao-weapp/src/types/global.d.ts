/* ================================================
 *  全局类型声明 — Taro + SCSS + 小程序特有属性
 * ================================================ */

/* ---- @tarojs/taro ---- */
declare module '@tarojs/taro' {
  interface ChooseImageOptions {
    count?: number
    sizeType?: string[]
    sourceType?: string[]
    success?: (res: ChooseImageResult) => void
    fail?: (err: any) => void
  }
  interface ChooseImageResult {
    tempFilePaths: string[]
    tempFiles: { path: string; size: number }[]
  }
  interface ShowActionSheetOptions {
    itemList: string[]
    success?: (res: { tapIndex: number }) => void
    fail?: (err: any) => void
  }
  interface LoginResult {
    code: string
    errMsg?: string
  }
  interface RequestResult {
    data: any
    statusCode: number
    header: Record<string, string>
  }
  interface UploadFileResult {
    data: string
    statusCode: number
  }

  const Taro: {
    switchTab(params: { url: string }): void
    reLaunch(params: { url: string }): void
    navigateTo(params: { url: string }): void
    navigateBack(params?: { delta?: number }): void
    showToast(params: { title: string; icon?: 'success' | 'error' | 'none' | 'loading'; duration?: number }): void
    showModal(params: { title: string; content: string; showCancel?: boolean; success?: (res: { confirm: boolean }) => void }): void
    showLoading(params: { title: string; mask?: boolean }): void
    hideLoading(): void
    showActionSheet(params: ShowActionSheetOptions): void
    login(): Promise<LoginResult>
    chooseImage(params: ChooseImageOptions): any
    uploadFile(params: {
      url: string
      filePath: string
      name: string
      header?: Record<string, string>
    }): Promise<UploadFileResult>
    getStorageSync(key: string): any
    setStorageSync(key: string, data: any): void
    removeStorageSync(key: string): void
    request(params: {
      url: string
      method?: string
      data?: any
      header?: Record<string, string>
      dataType?: string
      timeout?: number
    }): Promise<RequestResult>
    requestPayment(params: {
      timeStamp: string
      nonceStr: string
      package: string
      signType: string
      paySign: string
      success?: (res: any) => void
      fail?: (err: any) => void
    }): any
    setClipboardData(params: {
      data: string
      success?: () => void
      fail?: (err: any) => void
    }): any
    shareAppMessage(params?: { title?: string; path?: string; imageUrl?: string }): void
    getSystemInfoSync(): {
      windowWidth: number
      windowHeight: number
      pixelRatio: number
      platform: string
      model: string
    }
    canvasToTempFilePath(params: {
      canvasId?: string
      canvas?: any
      x?: number
      y?: number
      width?: number
      height?: number
      destWidth?: number
      destHeight?: number
      fileType?: string
      quality?: number
      success?: (res: { tempFilePath: string }) => void
      fail?: (err: any) => void
    }): any
    saveImageToPhotosAlbum(params: {
      filePath: string
      success?: () => void
      fail?: (err: any) => void
    }): any
    pageScrollTo(params: { scrollTop: number; duration?: number }): void
    createCanvasContext(canvasId: string): any
    createSelectorQuery(): any
    getEnv(): string
    env: Record<string, string>
    onError?: (callback: (err: any) => void) => void
  }

  export default Taro
}

/* ---- @tarojs/components ---- */
declare module '@tarojs/components' {
  import { FC, ReactNode, CSSProperties } from 'react'

  export interface ViewProps {
    className?: string
    style?: CSSProperties | string
    onClick?: (e: any) => void
    children?: ReactNode
    hoverClass?: string
    hoverStayTime?: number
    hoverStartTime?: number
  }
  export interface TextProps {
    className?: string
    children?: ReactNode
    onClick?: (e: any) => void
    style?: CSSProperties | string
    numberOfLines?: number
    selectable?: boolean
    decode?: boolean
  }
  export interface ImageProps {
    className?: string
    src?: string
    mode?: 'scaleToFill' | 'aspectFit' | 'aspectFill' | 'widthFix' | 'heightFix' | 'top' | 'bottom' | 'center' | 'left' | 'right'
    style?: CSSProperties | string
    onClick?: (e: any) => void
    onLoad?: (e: any) => void
    onError?: (e: any) => void
    lazyLoad?: boolean
    showMenuByLongpress?: boolean
  }
  export interface ButtonProps {
    className?: string
    type?: 'primary' | 'default' | 'warn'
    size?: 'default' | 'mini'
    loading?: boolean
    disabled?: boolean
    plain?: boolean
    openType?: 'contact' | 'share' | 'getPhoneNumber' | 'getUserInfo' | 'launchApp' | 'openSetting' | 'feedback'
    onClick?: (e: any) => void
    onGetPhoneNumber?: (e: any) => void
    onGetUserInfo?: (e: any) => void
    children?: ReactNode
    style?: CSSProperties | string
  }
  export interface InputProps {
    className?: string
    type?: 'text' | 'number' | 'idcard' | 'digit' | 'safe-password'
    value?: string
    placeholder?: string
    placeholderClass?: string
    placeholderStyle?: string
    disabled?: boolean
    maxlength?: number
    focus?: boolean
    password?: boolean
    'confirm-type'?: 'send' | 'search' | 'next' | 'go' | 'done'
    confirmType?: 'send' | 'search' | 'next' | 'go' | 'done'
    confirmHold?: boolean
    onInput?: (e: { detail: { value: string } }) => void
    onFocus?: (e: any) => void
    onBlur?: (e: any) => void
    onConfirm?: (e: any) => void
    style?: CSSProperties | string
  }
  export interface ScrollViewProps {
    className?: string
    scrollX?: boolean
    scrollY?: boolean
    scrollTop?: number
    scrollLeft?: number
    scrollIntoView?: string
    scrollWithAnimation?: boolean
    enhanced?: boolean
    showScrollbar?: boolean
    lowerThreshold?: number
    upperThreshold?: number
    refresherEnabled?: boolean
    refresherTriggered?: boolean
    onScrollToUpper?: () => void
    onScrollToLower?: () => void
    onScroll?: (e: any) => void
    onRefresherRefresh?: () => void
    children?: ReactNode
    style?: CSSProperties | string
  }
  export interface FormProps {
    className?: string
    onSubmit?: (e: any) => void
    onReset?: (e: any) => void
    reportSubmit?: boolean
    children?: ReactNode
  }
  export interface SwiperProps {
    className?: string
    indicatorDots?: boolean
    indicatorColor?: string
    indicatorActiveColor?: string
    autoplay?: boolean
    current?: number
    interval?: number
    duration?: number
    circular?: boolean
    vertical?: boolean
    onChange?: (e: any) => void
    children?: ReactNode
  }
  export interface SwiperItemProps {
    className?: string
    children?: ReactNode
  }
  export interface CanvasProps {
    className?: string
    style?: CSSProperties | string
    canvasId?: string
    type?: string
    ref?: any
    onTouchStart?: (e: any) => void
    onTouchMove?: (e: any) => void
    onTouchEnd?: (e: any) => void
  }
  export interface PickerProps {
    className?: string
    mode?: 'selector' | 'multiSelector' | 'time' | 'date' | 'region'
    range?: any[]
    rangeKey?: string
    value?: any
    onChange?: (e: any) => void
    children?: ReactNode
  }
  export interface CheckboxGroupProps {
    className?: string
    onChange?: (e: any) => void
    children?: ReactNode
  }
  export interface CheckboxProps {
    className?: string
    value?: string
    checked?: boolean
    disabled?: boolean
    color?: string
    children?: ReactNode
  }
  export interface RadioGroupProps {
    className?: string
    onChange?: (e: any) => void
    children?: ReactNode
  }
  export interface RadioProps {
    className?: string
    value?: string
    checked?: boolean
    disabled?: boolean
    color?: string
    children?: ReactNode
  }
  export interface LabelProps {
    className?: string
    for?: string
    children?: ReactNode
  }
  export interface NavigatorProps {
    className?: string
    url?: string
    openType?: 'navigate' | 'redirect' | 'switchTab' | 'reLaunch' | 'navigateBack'
    children?: ReactNode
  }
  export interface RichTextProps {
    className?: string
    nodes?: any
    children?: ReactNode
  }
  export interface VideoProps {
    className?: string
    src?: string
    controls?: boolean
    autoplay?: boolean
    loop?: boolean
    muted?: boolean
    style?: CSSProperties | string
  }
  export interface CoverViewProps {
    className?: string
    children?: ReactNode
  }
  export interface CoverImageProps {
    className?: string
    src?: string
    children?: ReactNode
  }
  export interface SlotProps {
    name?: string
    children?: ReactNode
  }

  export const View: FC<ViewProps>
  export const Text: FC<TextProps>
  export const Image: FC<ImageProps>
  export const Button: FC<ButtonProps>
  export const Input: FC<InputProps>
  export const ScrollView: FC<ScrollViewProps>
  export const Form: FC<FormProps>
  export const Swiper: FC<SwiperProps>
  export const SwiperItem: FC<SwiperItemProps>
  export const Canvas: FC<CanvasProps>
  export const Picker: FC<PickerProps>
  export const CheckboxGroup: FC<CheckboxGroupProps>
  export const Checkbox: FC<CheckboxProps>
  export const RadioGroup: FC<RadioGroupProps>
  export const Radio: FC<RadioProps>
  export const Label: FC<LabelProps>
  export const Navigator: FC<NavigatorProps>
  export const RichText: FC<RichTextProps>
  export const Video: FC<VideoProps>
  export const CoverView: FC<CoverViewProps>
  export const CoverImage: FC<CoverImageProps>
  export const Slot: FC<SlotProps>
  export const Block: FC<{ children?: ReactNode }>
}

/* ---- SCSS modules ---- */
declare module '*.scss' {
  const content: Record<string, string>
  export default content
}
declare module '*.css' {
  const content: Record<string, string>
  export default content
}
declare module '*.less' {
  const content: Record<string, string>
  export default content
}

/* ---- Global runtime APIs (小程序环境) ---- */
declare function setTimeout(callback: (...args: any[]) => void, ms: number, ...args: any[]): number
declare function clearTimeout(timeoutId: number | undefined): void
declare function setInterval(callback: (...args: any[]) => void, ms: number, ...args: any[]): number
declare function clearInterval(intervalId: number | undefined): void
declare var console: { log: (...args: any[]) => void; error: (...args: any[]) => void; warn: (...args: any[]) => void; info: (...args: any[]) => void; debug: (...args: any[]) => void }
declare var process: { env: Record<string, string | undefined> }
