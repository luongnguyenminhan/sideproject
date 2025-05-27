"use client"

import React, { useState } from "react"
import { Search, Eye, EyeOff, Mail, Lock, User, Settings, LogOut } from "lucide-react"
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  Input,
  InputWithIcon,
} from "@/components/ui"

export default function DemoComponents() {
  const [showPassword, setShowPassword] = useState(false)
  const [searchValue, setSearchValue] = useState("")

  return (
    <div className="container mx-auto p-8 space-y-12">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-foreground">UI Components Demo</h1>
        <p className="text-muted-foreground text-lg">
          Showcase của các UI components được tạo cho dự án
        </p>
      </div>

      {/* Buttons Section */}
      <section className="space-y-6">
        <h2 className="text-2xl font-semibold text-foreground">Buttons</h2>
        <Card>
          <CardHeader>
            <CardTitle>Button Variants</CardTitle>
            <CardDescription>Các loại button khác nhau với variants và sizes</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-4">
              <Button variant="default">Default</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="destructive">Destructive</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="link">Link</Button>
            </div>
            
            <div className="flex flex-wrap gap-4 items-center">
              <Button size="sm">Small</Button>
              <Button size="default">Default</Button>
              <Button size="lg">Large</Button>
              <Button size="icon">
                <Settings className="h-4 w-4" />
              </Button>
            </div>

            <div className="flex gap-4">
              <Button disabled>Disabled</Button>
              <Button variant="outline" disabled>Disabled Outline</Button>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Dropdown Menu Section */}
      <section className="space-y-6">
        <h2 className="text-2xl font-semibold text-foreground">Dropdown Menu</h2>
        <Card>
          <CardHeader>
            <CardTitle>Dropdown Examples</CardTitle>
            <CardDescription>Các ví dụ về dropdown menu với items khác nhau</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-4">
              {/* Basic Dropdown */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline">
                    <User className="mr-2 h-4 w-4" />
                    User Menu
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuLabel>My Account</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem>
                    <User className="mr-2 h-4 w-4" />
                    Profile
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Settings className="mr-2 h-4 w-4" />
                    Settings
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem className="text-destructive">
                    <LogOut className="mr-2 h-4 w-4" />
                    Log out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              {/* Settings Dropdown */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <Settings className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem>Edit</DropdownMenuItem>
                  <DropdownMenuItem>Duplicate</DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem className="text-destructive">Delete</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Input Section */}
      <section className="space-y-6">
        <h2 className="text-2xl font-semibold text-foreground">Input Fields</h2>
        <Card>
          <CardHeader>
            <CardTitle>Input Examples</CardTitle>
            <CardDescription>Các loại input field với và không có icon</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Basic Inputs */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Basic Input</label>
                <Input placeholder="Enter your name..." />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">Disabled Input</label>
                <Input placeholder="Disabled input" disabled />
              </div>
            </div>

            {/* Inputs with Icons */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Email with Icon</label>
                <InputWithIcon
                  type="email"
                  placeholder="Enter your email..."
                  leftIcon={<Mail className="h-4 w-4" />}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Search with Icon</label>
                <InputWithIcon
                  type="text"
                  placeholder="Search..."
                  leftIcon={<Search className="h-4 w-4" />}
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                  rightIcon={searchValue ? <Button variant="ghost" size="icon" className="h-6 w-6">×</Button> : undefined}
                  onRightIconClick={() => setSearchValue("")}
                />
              </div>
            </div>

            {/* Password Input */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Password</label>
                <InputWithIcon
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter password..."
                  leftIcon={<Lock className="h-4 w-4" />}
                  rightIcon={showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  onRightIconClick={() => setShowPassword(!showPassword)}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Username</label>
                <InputWithIcon
                  type="text"
                  placeholder="@username"
                  leftIcon={<User className="h-4 w-4" />}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Cards Section */}
      <section className="space-y-6">
        <h2 className="text-2xl font-semibold text-foreground">Cards</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Simple Card */}
          <Card>
            <CardHeader>
              <CardTitle>Simple Card</CardTitle>
              <CardDescription>A basic card with title and description</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                This is a simple card content. You can put any content here.
              </p>
            </CardContent>
          </Card>

          {/* Card with Footer */}
          <Card>
            <CardHeader>
              <CardTitle>Card with Footer</CardTitle>
              <CardDescription>A card that includes a footer section</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                This card includes a footer with action buttons.
              </p>
            </CardContent>
            <CardFooter className="gap-2">
              <Button variant="outline" size="sm">Cancel</Button>
              <Button size="sm">Save</Button>
            </CardFooter>
          </Card>

          {/* Interactive Card */}
          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle>Interactive Card</CardTitle>
              <CardDescription>Hover to see the effect</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center">
                  <Settings className="h-6 w-6 text-primary-foreground" />
                </div>
                <div>
                  <p className="font-semibold">Feature</p>
                  <p className="text-sm text-muted-foreground">Description of the feature</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Combined Example */}
      <section className="space-y-6">
        <h2 className="text-2xl font-semibold text-foreground">Combined Example</h2>
        <Card className="max-w-md mx-auto">
          <CardHeader>
            <CardTitle>Login Form</CardTitle>
            <CardDescription>Ví dụ kết hợp tất cả components</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Email</label>
              <InputWithIcon
                type="email"
                placeholder="Enter your email"
                leftIcon={<Mail className="h-4 w-4" />}
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Password</label>
              <InputWithIcon
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                leftIcon={<Lock className="h-4 w-4" />}
                rightIcon={showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                onRightIconClick={() => setShowPassword(!showPassword)}
              />
            </div>
          </CardContent>
          <CardFooter className="flex-col gap-2">
            <Button className="w-full">Sign In</Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="w-full">
                  More Options
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem>Forgot Password</DropdownMenuItem>
                <DropdownMenuItem>Create Account</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem>Help</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </CardFooter>
        </Card>
      </section>
    </div>
  )
} 