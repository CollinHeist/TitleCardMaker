import DefaultLayout from "@/layouts/default";
import { Button, Checkbox, Divider, Input, Select, SelectItem } from "@nextui-org/react";
import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { api, getConnections } from './api/api';

export default function IndexPage() {

  let connections = [
    {label: 'Jellyfin', value: 1, description: 'Emby'},
    {label: 'Plex', value: 2},
    {label: 'Sonarr', value: 3},
    {label: 'TMDb', value: 4},
  ]
  const [isLoading, setIsLoading] = useState(false);
  const [settings, setSettings] = useState({
    // Initial values
    card_directory: '',
    source_directory: '',
    completely_delete_series: false,
    episode_data_source: 1,
  });

  useEffect(() => {
    api.get('/settings/settings')
      .then(response => {
        setSettings(response.data);
      })
      .catch(error => {
        console.log(error);
      })
    ;

    // api.get('/connections/all')
    //   .then(response => {
    //     connections = response.data;
    //   })
    // ;
  }, []);

  const handleChangeInput = (event: ChangeEvent) => {
    const value = event.target.type === 'checkbox'
      ? event.target.checked
      : event.target.value;
    setSettings({
      ...settings,
      [event.target.name]: value,
    });
  };
  const handleFormSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setIsLoading(true);
    api.patch('/settings/update', settings)
      .finally(() => {
        setTimeout(() => setIsLoading(false), 1000);
      })
    ;
  };

  return (
    <DefaultLayout>
      <form onSubmit={handleFormSubmit}>
        <Input
          name="card_directory"
          label="Title Card Directory"
          type="text"
          isRequired
          description="Directory to store all Title Cards. Can be overrwitten per-Series."
          value={settings.card_directory}
          variant="bordered"
          // className="max-w-xs"
          onChange={handleChangeInput}
        />

        <Input
          name="source_directory"
          label="Source Directory"
          type="text"
          isRequired
          description="Directory to store all textless source images."
          value={settings.source_directory}
          variant="bordered"
          // className="max-w-xs"
          onChange={handleChangeInput}
        />

        <Checkbox
          name="completely_delete_series"
          defaultSelected={settings.completely_delete_series}
          onChange={handleChangeInput}
        >
          Delete Series Source Images
        </Checkbox>

        <Divider className="my-4"/>

        <Select
          items={connections}
          label="Episode Data Source"
          placeholder="Select a Connection"
          selectionMode="single"
          value={settings.episode_data_source}
          className="max-w-xs"
        >
          {(connections) => <SelectItem key={connections.value}>{connections.label}</SelectItem>}
        </Select>

        <Divider className="my-4"/>

        <Button
          type="submit"
          color="primary"
          isLoading={isLoading}
          variant="ghost">
          Save Changes
        </Button>
      </form>
    </DefaultLayout>
  );
}
