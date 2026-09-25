import { SortableContainer } from 'react-sortable-hoc'

const SortableBody = SortableContainer(props => <tbody {...props} />)

const arrayMoveImmutable = (array, oldIndex, newIndex) => {
    const newArray = [...array]
    const [item] = newArray.splice(oldIndex, 1)
    newArray.splice(newIndex, 0, item)
    return newArray
}

export const DraggableContainer = ({ props, setDataSource }) => {

    const onSortEnd = ({ oldIndex, newIndex }) => {
        if (oldIndex !== newIndex) {
            setDataSource(prev => arrayMoveImmutable(prev.slice(), oldIndex, newIndex))
        }
    }

    return <SortableBody useDragHandle disableAutoscroll helperClass='row-dragging' onSortEnd={onSortEnd} {...props} />
}