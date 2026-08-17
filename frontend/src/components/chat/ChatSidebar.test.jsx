import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import ChatSidebar from './ChatSidebar'

describe('mobile conversation history', () => {
  it('selects a conversation and exposes a keyboard-labeled close action', () => {
    const select = vi.fn()
    const close = vi.fn()
    render(
      <ChatSidebar
        mobileOpen
        chats={[{ id: 'conv_1', title: 'Thermodynamics' }]}
        onSelectChat={select}
        onMobileClose={close}
      />,
    )
    expect(screen.getByRole('button', { name: 'Close conversation history' })).toBeInTheDocument()
    fireEvent.click(screen.getByText('Thermodynamics'))
    expect(select).toHaveBeenCalledWith('conv_1')
    expect(close).toHaveBeenCalledOnce()
  })
})
