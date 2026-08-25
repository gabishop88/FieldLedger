import { Card, Center, Text } from "@mantine/core"

export function NotLoggedInCard() {
  return <Center h="100%">
    <Card withBorder shadow="md" maw={420} ta="center">
      <Text fw={600} p="md">Not Logged In</Text>

      <Text c="dimmed">
        Log in with your FieldLedger account, or make a new one,
        by clicking the 'Log In' button in the top right.
      </Text>
    </Card>
  </Center>
}

export function NotConnectedCard() {
  return <Center h="100%">
    <Card withBorder shadow="md" maw={420} ta="center">
      <Text fw={600} p="md">Not Connected to John Deere</Text>

      <Text c="dimmed">
        Click the 'Connect John Deere' Button in the top left
        to connect your FieldLedger account to your John Deere
        account and start the syncing process.
      </Text>
    </Card>
  </Center>
}

export function FieldNotSelectedCard() {
  return <Center h="100%">
    <Card withBorder shadow="md" maw={420} ta="center">
      <Text fw={600} p="md">No Field Selected</Text>

      <Text c="dimmed">
        Select a synced field from the tree to
        browse Operations & Boundaries.
      </Text>
    </Card>
  </Center>
}

export function EmptyOpCard() {
  return <Center h="100%" flex={1}>
    <Card withBorder shadow="md" maw={420} ta="center">
      <Text fw={600} p="md">No Operation Selected</Text>

      <Text c="dimmed">
        Select an operation from the timeline to
        see sync options and more details.
      </Text>

      <Text c="dimmed" pt="md">
        Or, select a Field Boundary above.
      </Text>
    </Card>
  </Center>
}